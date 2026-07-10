"""Native Bambu Lab LAN-mode driver (Section 9.8 / 12).

Talks directly to a Bambu Lab printer (A1 Mini) over the local services
its "LAN Only Mode" + "Developer Mode" expose, with no cloud/OctoPrint
in between:

- MQTT over TLS on port 8883, username ``bblp``, password = the
  printer's LAN access code. The broker uses a self-signed certificate,
  so we don't verify it (this is a LAN-only protocol with no public CA
  anyway). Status reports arrive on ``device/{serial}/report``;
  commands are published to ``device/{serial}/request``.
- FTPS (implicit TLS, port 990) for transferring a sliced artifact onto
  the printer's internal storage before printing it.

Bambu Lab doesn't publish this protocol; the topic/payload shapes below
follow community reverse-engineering (see e.g.
https://github.com/Doridian/OpenBambuAPI/blob/main/mqtt.md). MVP scope
per Section 9.8 is deliberately narrow: get_status/upload_artifact/
start_print/cancel_print (pause/resume are implemented best-effort
since the shared `PrinterDriver` interface requires them, but are not
part of the MVP acceptance criteria).
"""

from __future__ import annotations

import json
import ssl
import time
import uuid
from ftplib import FTP_TLS
from pathlib import Path

import paho.mqtt.client as mqtt

from app.core.crypto import decrypt_secret
from app.models.printer import Printer
from app.printer_drivers.base import (
    PrinterConnectionError,
    PrinterDriver,
    PrinterDriverError,
    PrinterStatus,
    Temperatures,
)

DEFAULT_MQTT_PORT = 8883
DEFAULT_FTPS_PORT = 990
MQTT_USERNAME = "bblp"
CONNECT_TIMEOUT_SECONDS = 5
REPORT_WAIT_SECONDS = 4
POLL_INTERVAL_SECONDS = 0.1

# Bambu's `print.gcode_state` values, mapped onto our driver-agnostic
# `PrinterStatus`. Unknown/missing states are treated as OFFLINE so a
# printer that's unreachable doesn't get misread as IDLE.
_GCODE_STATE_MAP = {
    "IDLE": PrinterStatus.IDLE,
    "PREPARE": PrinterStatus.PRINTING,
    "RUNNING": PrinterStatus.PRINTING,
    "PAUSE": PrinterStatus.PAUSED,
    "FINISH": PrinterStatus.FINISHED,
    "FAILED": PrinterStatus.ERROR,
}


class BambuLanDriver(PrinterDriver):
    """A fresh instance is created per call (Section 9.7); each one owns
    its own short-lived MQTT/FTPS connections and a small report cache
    so `get_status`/`get_progress`/`get_temperatures` called back-to-back
    on the same instance only need a single round trip to the printer."""

    def __init__(self, printer: Printer) -> None:
        super().__init__(printer)
        self._cached_report: dict | None = None

    def _access_code(self) -> str:
        if not self.printer.access_code_encrypted:
            raise PrinterConnectionError(f"Printer '{self.printer.name}' has no access code set.")
        return decrypt_secret(self.printer.access_code_encrypted)

    def _host(self) -> str:
        if not self.printer.host:
            raise PrinterConnectionError(f"Printer '{self.printer.name}' has no host configured.")
        return self.printer.host

    def _mqtt_port(self) -> int:
        return self.printer.port or DEFAULT_MQTT_PORT

    def _serial(self) -> str:
        if not self.printer.serial_number:
            raise PrinterConnectionError(
                f"Printer '{self.printer.name}' has no serial number configured."
            )
        return self.printer.serial_number

    def _new_mqtt_client(self) -> mqtt.Client:
        client = mqtt.Client(client_id=f"schoolprint-{uuid.uuid4().hex[:8]}")
        client.username_pw_set(MQTT_USERNAME, self._access_code())
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)
        return client

    def test_connection(self) -> bool:
        client = self._new_mqtt_client()
        state = {"connected": False}
        client.on_connect = lambda _c, _u, _f, rc: state.update(connected=(rc == 0))
        try:
            client.connect(self._host(), self._mqtt_port(), keepalive=CONNECT_TIMEOUT_SECONDS)
            client.loop_start()
            deadline = time.monotonic() + CONNECT_TIMEOUT_SECONDS
            while time.monotonic() < deadline and not state["connected"]:
                time.sleep(POLL_INTERVAL_SECONDS)
        except OSError as exc:
            raise PrinterConnectionError(f"Could not reach printer: {exc}") from exc
        finally:
            client.loop_stop()
            client.disconnect()
        return state["connected"]

    def upload_artifact(self, local_path: Path, remote_name: str) -> None:
        if not local_path.exists():
            raise FileNotFoundError(f"Artifact not found: {local_path}")
        try:
            ftp = FTP_TLS()
            ftp.connect(self._host(), DEFAULT_FTPS_PORT, timeout=CONNECT_TIMEOUT_SECONDS)
            ftp.login(MQTT_USERNAME, self._access_code())
            ftp.prot_p()
            with local_path.open("rb") as fh:
                ftp.storbinary(f"STOR {remote_name}", fh)
            ftp.quit()
        except OSError as exc:
            raise PrinterDriverError(f"Failed to upload artifact to printer: {exc}") from exc

    def _publish_command(self, payload: dict) -> None:
        client = self._new_mqtt_client()
        try:
            client.connect(self._host(), self._mqtt_port(), keepalive=CONNECT_TIMEOUT_SECONDS)
            client.loop_start()
            client.publish(f"device/{self._serial()}/request", json.dumps(payload), qos=1)
            time.sleep(0.5)  # give paho a moment to flush the publish before disconnecting
        except OSError as exc:
            raise PrinterDriverError(f"Failed to send command to printer: {exc}") from exc
        finally:
            client.loop_stop()
            client.disconnect()

    def start_print(self, remote_name: str) -> None:
        self._cached_report = None
        self._publish_command(
            {
                "print": {
                    "sequence_id": "0",
                    "command": "project_file",
                    "url": f"ftp:///{remote_name}",
                    "param": "Metadata/plate_1.gcode",
                    "project_id": "0",
                    "profile_id": "0",
                    "task_id": "0",
                    "subtask_id": "0",
                    "md5": "",
                    "timelapse": False,
                    "bed_type": "auto",
                    "bed_leveling": True,
                    "flow_cali": True,
                    "vibration_cali": True,
                    "layer_inspect": True,
                    "use_ams": False,
                }
            }
        )

    def pause(self) -> None:
        self._cached_report = None
        self._publish_command({"print": {"sequence_id": "0", "command": "pause"}})

    def resume(self) -> None:
        self._cached_report = None
        self._publish_command({"print": {"sequence_id": "0", "command": "resume"}})

    def cancel_print(self) -> None:
        self._cached_report = None
        self._publish_command({"print": {"sequence_id": "0", "command": "stop"}})

    def _fetch_report(self) -> dict:
        if self._cached_report is not None:
            return self._cached_report

        client = self._new_mqtt_client()
        received: dict[str, dict] = {}

        def _on_message(_client, _userdata, msg) -> None:
            try:
                data = json.loads(msg.payload.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return
            if "print" in data:
                received["print"] = data["print"]

        def _on_connect(connected_client, _userdata, _flags, rc) -> None:
            if rc == 0:
                connected_client.subscribe(f"device/{self._serial()}/report")
                connected_client.publish(
                    f"device/{self._serial()}/request",
                    json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}),
                )

        client.on_connect = _on_connect
        client.on_message = _on_message
        try:
            client.connect(self._host(), self._mqtt_port(), keepalive=CONNECT_TIMEOUT_SECONDS)
            client.loop_start()
            deadline = time.monotonic() + REPORT_WAIT_SECONDS
            while time.monotonic() < deadline and "print" not in received:
                time.sleep(POLL_INTERVAL_SECONDS)
        except OSError as exc:
            raise PrinterConnectionError(f"Could not reach printer: {exc}") from exc
        finally:
            client.loop_stop()
            client.disconnect()

        if "print" not in received:
            raise PrinterConnectionError(
                f"Printer '{self.printer.name}' did not send a status report in time."
            )
        self._cached_report = received["print"]
        return self._cached_report

    def get_status(self) -> PrinterStatus:
        gcode_state = str(self._fetch_report().get("gcode_state", "")).upper()
        return _GCODE_STATE_MAP.get(gcode_state, PrinterStatus.OFFLINE)

    def get_progress(self) -> float:
        return float(self._fetch_report().get("mc_percent", 0) or 0)

    def get_temperatures(self) -> Temperatures:
        report = self._fetch_report()
        return Temperatures(
            nozzle_actual=float(report.get("nozzle_temper", 0) or 0),
            nozzle_target=float(report.get("nozzle_target_temper", 0) or 0),
            bed_actual=float(report.get("bed_temper", 0) or 0),
            bed_target=float(report.get("bed_target_temper", 0) or 0),
        )
