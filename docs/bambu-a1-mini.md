# Bambu Lab A1 Mini setup

SchoolPrint talks to the Bambu Lab A1 Mini directly over your local
network — no OctoPrint, no Bambu cloud account required for printing
(Section 12 / Section 20 Decision 1–2 of the design doc). This uses the
printer's own **LAN Only Mode** + **Developer Mode**, which expose an
MQTT broker and an FTPS server on the printer itself.

## 1. Enable LAN Mode and Developer Mode on the printer

On the printer's touchscreen:

1. Go to **Settings → Network → LAN Only Mode** and enable it.
   ([Bambu Lab: Enable LAN mode](https://wiki.bambulab.com/en/knowledge-sharing/enable-lan-mode))
2. Go to **Settings → General → Developer Mode** and enable it.
   ([Bambu Lab: Enable Developer mode](https://wiki.bambulab.com/en/knowledge-sharing/enable-developer-mode))
3. Open **Settings → Network** and note down:
   - The printer's **IP address** (give it a static IP or a DHCP
     reservation on your router so it doesn't change)
   - The **Access Code** shown on the LAN Mode screen
   - The **Device/Serial Number** (also under Settings, or on a label on
     the printer)

Developer Mode opens:

- MQTT over TLS on port **8883** (username `bblp`, password = the Access
  Code)
- FTPS (implicit TLS) on port **990**, same credentials

Both are LAN-only; nothing here talks to Bambu's cloud.

## 2. Add the printer in SchoolPrint

Log in as an admin, go to **Printers → Add printer**, and fill in:

```text
Name:            A1 Mini Raum 101
Driver:          Bambu Lab (LAN mode)
Host:            <the IP address you noted down>
Serial number:   <the device/serial number>
Access code:     <the access code>
```

`Host` and `Serial number` are required for the Bambu LAN driver; the
port defaults to `8883` and normally doesn't need to change.

The access code is **encrypted at rest** and is never shown again in the
UI after saving — if you need to change it, overwrite it (there is no
"reveal" option, by design, see [docs/security.md](security.md)).

## 3. Test the connection

Click **Test connection** next to the printer. This connects over MQTT
and confirms the broker accepts the credentials. If it fails:

- Double-check the IP address (try pinging it from the Pi)
- Confirm LAN Mode and Developer Mode are still enabled (the printer can
  reset these after a firmware update)
- Confirm the Pi and printer are on the same LAN/VLAN and that firewalls
  aren't blocking ports 8883/990

## 4. Print flow

Once connected, the normal SchoolPrint workflow applies:

1. A student uploads an `.stl` and a teacher approves it — SchoolPrint
   slices it with OrcaSlicer automatically.
2. The sliced job appears in the **Queue**.
3. A teacher clicks **Start print** on a queued job and picks this
   printer. SchoolPrint uploads the sliced `.gcode.3mf` to the printer
   over FTPS and sends an MQTT `project_file` print command.
4. Progress, temperatures, and status are polled live from the printer
   and shown on the **Queue** page and to the student on their job page.
5. Prints are **always started manually** by a teacher — the queue and
   slicing happen automatically, but nothing prints without a click
   (Section 20 Decision 5).

## Hardware test checklist

Before relying on this in a classroom, run through the design doc's
manual hardware checklist (Section 17):

- [ ] Printer is in LAN Mode with Developer Mode active
- [ ] "Test connection" succeeds in the SchoolPrint UI
- [ ] Printer status (temperatures, idle/printing state) shows correctly
- [ ] Upload a small test model end-to-end (upload → approve → slice →
      queue)
- [ ] Manually start the print from the Queue page
- [ ] Progress updates while printing
- [ ] The job shows `FINISHED` after the print completes, and the student
      sees "fertig gedruckt am `<date>`" on their job page

## Limitations (MVP)

- Only one Bambu Lab printer's AMS-less, single-plate print flow is
  supported end-to-end for the MVP; AMS/multi-material printing is not
  wired up.
- The protocol used here is based on community reverse-engineering (see
  the comment at the top of `backend/app/printer_drivers/bambu_lan.py`
  and [OpenBambuAPI](https://github.com/Doridian/OpenBambuAPI/blob/main/mqtt.md)),
  since Bambu Lab doesn't publish it officially — a firmware update could
  in principle change behavior.
