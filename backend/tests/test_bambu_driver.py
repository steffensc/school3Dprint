"""Unit tests for `BambuLanDriver` against a mocked MQTT broker + FTPS
server (Section 17 notes that hardware verification needs a real A1
Mini and can't run in this sandbox, so protocol behavior is verified
here instead).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

import app.printer_drivers.bambu_lan as bambu_lan_module
from app.models.enums import PrinterDriverType
from app.models.printer import Printer
from app.printer_drivers.bambu_lan import BambuLanDriver
from app.printer_drivers.base import PrinterConnectionError, PrinterStatus


class _FakeMqttClient:
    """Stands in for `paho.mqtt.client.Client`: "connects" synchronously,
    optionally auto-replies to a `pushall` request with a canned status
    report, and records every published payload for assertions."""

    report: dict | None = None
    fail_connect: bool = False

    def __init__(self, client_id: str | None = None) -> None:
        self.client_id = client_id
        self.on_connect = None
        self.on_message = None
        self.published: list[tuple[str, str]] = []
        self.subscriptions: list[str] = []

    def username_pw_set(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def tls_set(self, **kwargs) -> None:
        pass

    def tls_insecure_set(self, value: bool) -> None:
        pass

    def connect(self, host: str, port: int, keepalive: int = 60) -> None:
        if type(self).fail_connect:
            raise OSError("connection refused (simulated)")
        self.host = host
        self.port = port

    def loop_start(self) -> None:
        rc = 0
        if self.on_connect:
            self.on_connect(self, None, None, rc)

    def loop_stop(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def subscribe(self, topic: str) -> None:
        self.subscriptions.append(topic)

    def publish(self, topic: str, payload: str, qos: int = 0) -> None:
        self.published.append((topic, payload))
        decoded = json.loads(payload)
        if "pushing" in decoded and type(self).report is not None and self.on_message:
            message = _FakeMessage(topic.replace("/request", "/report"), type(self).report)
            self.on_message(self, None, message)


class _FakeMessage:
    def __init__(self, topic: str, report: dict) -> None:
        self.topic = topic
        self.payload = json.dumps({"print": report}).encode("utf-8")


@pytest.fixture()
def fake_mqtt(monkeypatch: pytest.MonkeyPatch):
    _FakeMqttClient.report = None
    _FakeMqttClient.fail_connect = False
    monkeypatch.setattr(bambu_lan_module.mqtt, "Client", _FakeMqttClient)
    yield _FakeMqttClient
    _FakeMqttClient.report = None
    _FakeMqttClient.fail_connect = False


@pytest.fixture()
def bambu_printer(db_session) -> Printer:
    printer = Printer(
        name="Test Bambu A1 Mini",
        driver_type=PrinterDriverType.BAMBU_LAN,
        host="10.0.0.42",
        serial_number="01P00A000000001",
        access_code_encrypted=None,
    )
    from app.core.crypto import encrypt_secret

    printer.access_code_encrypted = encrypt_secret("12345678")
    db_session.add(printer)
    db_session.commit()
    db_session.refresh(printer)
    return printer


def test_test_connection_succeeds_against_mocked_broker(fake_mqtt, bambu_printer) -> None:
    driver = BambuLanDriver(bambu_printer)
    assert driver.test_connection() is True


def test_test_connection_fails_when_broker_unreachable(fake_mqtt, bambu_printer) -> None:
    fake_mqtt.fail_connect = True
    driver = BambuLanDriver(bambu_printer)
    with pytest.raises(PrinterConnectionError):
        driver.test_connection()


def test_get_status_parses_report(fake_mqtt, bambu_printer) -> None:
    fake_mqtt.report = {
        "gcode_state": "RUNNING",
        "mc_percent": 42,
        "nozzle_temper": 210.4,
        "nozzle_target_temper": 210,
        "bed_temper": 59.8,
        "bed_target_temper": 60,
    }
    driver = BambuLanDriver(bambu_printer)
    assert driver.get_status() == PrinterStatus.PRINTING
    assert driver.get_progress() == 42
    temps = driver.get_temperatures()
    assert temps.nozzle_actual == 210.4
    assert temps.bed_target == 60


def test_get_status_maps_unknown_state_to_offline(fake_mqtt, bambu_printer) -> None:
    fake_mqtt.report = {"gcode_state": "SOMETHING_NEW"}
    driver = BambuLanDriver(bambu_printer)
    assert driver.get_status() == PrinterStatus.OFFLINE


def test_get_status_raises_when_printer_never_reports(fake_mqtt, bambu_printer) -> None:
    fake_mqtt.report = None
    driver = BambuLanDriver(bambu_printer)
    with pytest.raises(PrinterConnectionError):
        driver.get_status()


def test_report_is_cached_within_one_driver_instance(
    fake_mqtt, bambu_printer, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_mqtt.report = {"gcode_state": "IDLE", "mc_percent": 0}
    pushall_count = {"n": 0}
    original_publish = _FakeMqttClient.publish

    def _counting_publish(self, topic, payload, qos=0):
        if "pushing" in json.loads(payload):
            pushall_count["n"] += 1
        return original_publish(self, topic, payload, qos)

    monkeypatch.setattr(_FakeMqttClient, "publish", _counting_publish)

    driver = BambuLanDriver(bambu_printer)
    driver.get_status()
    driver.get_progress()
    driver.get_temperatures()

    assert pushall_count["n"] == 1


def test_pause_resume_cancel_publish_expected_commands(
    fake_mqtt, bambu_printer, monkeypatch
) -> None:
    captured: list[tuple[str, str]] = []

    original_publish = _FakeMqttClient.publish

    def _capturing_publish(self, topic, payload, qos=0):
        captured.append((topic, payload))
        return original_publish(self, topic, payload, qos)

    monkeypatch.setattr(_FakeMqttClient, "publish", _capturing_publish)

    driver = BambuLanDriver(bambu_printer)
    driver.start_print("job123.gcode.3mf")
    driver.pause()
    driver.resume()
    driver.cancel_print()

    commands = [json.loads(payload)["print"]["command"] for _topic, payload in captured]
    assert commands == ["project_file", "pause", "resume", "stop"]

    start_payload = json.loads(captured[0][1])["print"]
    assert start_payload["url"] == "ftp:///job123.gcode.3mf"


def test_upload_artifact_uses_ftps(
    monkeypatch: pytest.MonkeyPatch, bambu_printer, tmp_path: Path
) -> None:
    stored: dict[str, object] = {}

    class _FakeFTPTLS:
        def connect(self, host, port, timeout=None):
            stored["connected"] = (host, port)

        def login(self, user, password):
            stored["login"] = (user, password)

        def prot_p(self):
            stored["prot_p"] = True

        def storbinary(self, command, fh):
            stored["storbinary"] = command
            stored["data"] = fh.read()

        def quit(self):
            stored["quit"] = True

    monkeypatch.setattr(bambu_lan_module, "FTP_TLS", _FakeFTPTLS)

    artifact = tmp_path / f"{uuid.uuid4()}.gcode.3mf"
    artifact.write_bytes(b"fake-gcode-3mf-content")

    driver = BambuLanDriver(bambu_printer)
    driver.upload_artifact(artifact, artifact.name)

    assert stored["connected"] == ("10.0.0.42", 990)
    assert stored["login"] == ("bblp", "12345678")
    assert stored["storbinary"] == f"STOR {artifact.name}"
    assert stored["data"] == b"fake-gcode-3mf-content"


def test_upload_artifact_missing_file_raises(bambu_printer, tmp_path: Path) -> None:
    driver = BambuLanDriver(bambu_printer)
    with pytest.raises(FileNotFoundError):
        driver.upload_artifact(tmp_path / "does-not-exist.gcode.3mf", "does-not-exist.gcode.3mf")


def test_missing_access_code_raises_connection_error(db_session) -> None:
    printer = Printer(
        name="No Access Code",
        driver_type=PrinterDriverType.BAMBU_LAN,
        host="10.0.0.99",
        serial_number="01P00A000000002",
    )
    db_session.add(printer)
    db_session.commit()
    db_session.refresh(printer)

    driver = BambuLanDriver(printer)
    with pytest.raises(PrinterConnectionError):
        driver.test_connection()
