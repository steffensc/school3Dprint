## Plan: MVP für lokalen Schul-3D-Druckserver

**TL;DR:**  
Baue eine lokale Webanwendung auf dem Raspberry Pi, die den kompletten schulgeeigneten Workflow abbildet: User laden STL-Dateien hoch, Lehrer prüfen und geben frei, Druckaufträge werden in einer Warteschlange verwaltet, und Drucke werden manuell über das Webinterface gestartet. Für den MVP würde ich **FastAPI + PostgreSQL + React + shadcn/ui + OrcaSlicer CLI + nativen Bambu-LAN-Treiber** verwenden. Der Bambu Lab A1 Mini wird nicht über OctoPrint gesteuert, sondern über lokales LAN/Developer-Mode-Protokoll, da Bambu LAN Mode lokale Kommunikation ohne Cloud ermöglicht und Developer Mode MQTT/FTP öffnet. https://wiki.bambulab.com/en/knowledge-sharing/enable-lan-mode, https://wiki.bambulab.com/en/knowledge-sharing/enable-developer-mode

***

# 1. MVP-Zielbild

## Ziel

Ein lokales, schulgeeignetes 3D-Druck-Management-System mit:

* Login
* Rollen: `ADMIN`, `USER`
* User-Upload von `.stl`
* Userübersicht eigener Druckaufträge
* Lehrer-Adminbereich
* Freigabeprozess
* Manuell startbare Druckwarteschlange
* Mehrdruckerfähigkeit
* Lokaler Dateispeicherung auf dem Raspberry Pi
* Retention/Löschung alter Dateien
* Bambu Lab A1 Mini als erster unterstützter Drucker
* Podman-Deployment
* Update-Prüfung und Update-Installation über Webinterface

***

# 2. Technische Grundentscheidung

## Backend

**Python + FastAPI**

Begründung:

* Sehr gut geeignet für moderne REST APIs
* Automatische OpenAPI-Dokumentation
* Gute Typisierung mit Pydantic
* Sehr gut containerisierbar

## Datenbank

**PostgreSQL**

Begründung:

* Robuster als SQLite für Warteschlangen, Nutzerverwaltung und spätere Mehrdruckerfähigkeit
* Läuft auf Raspberry Pi 5 problemlos
* Gute Migrationen mit Alembic

Alembic ist das etablierte Migrationstool für SQLAlchemy und versioniert Datenbankschema-Änderungen sauber. https://alembic.sqlalchemy.org/en/latest/

## ORM/Migrationen

* SQLAlchemy 2.x
* Alembic

## Frontend

**React + TypeScript + shadcn/ui**

Begründung:

* Moderne, saubere UI
* Fertige Komponenten für Buttons, Dialoge, Tabellen, Menüs, Formulare
* Gut geeignet für Admin-Dashboards
* Später leicht erweiterbar

## Slicer

**OrcaSlicer CLI**

OrcaSlicer besitzt eine CLI-/Headless-Nutzung für automatisiertes Slicing; wichtige Optionen wie `--load-settings`, `--load-filaments`, `--slice` und `--export-3mf` werden in der Community bereits für automatisierte Workflows genutzt. https://github.com/OrcaSlicer/OrcaSlicer/discussions/1603, https://github.com/OrcaSlicer/OrcaSlicer/discussions/8593

## Druckeranbindung MVP

**Native Bambu-LAN-Anbindung**

Der Bambu Lab A1 Mini soll nicht über OctoPrint angebunden werden. Bambu LAN Mode erlaubt lokale Kommunikation im Netzwerk; Developer Mode öffnet MQTT, Live Stream und FTP für lokale Steuerung. https://wiki.bambulab.com/en/knowledge-sharing/enable-lan-mode, https://wiki.bambulab.com/en/knowledge-sharing/enable-developer-mode

***

# 3. High-Level-Architektur

```text
Tablet / Browser
        │
        ▼
React Web UI
        │
        ▼
FastAPI Backend
        │
        ├── PostgreSQL
        ├── Lokaler Dateispeicher
        ├── OrcaSlicer CLI
        ├── Bambu Printer Driver
        └── Update Manager
                │
                ▼
        Bambu Lab A1 Mini im lokalen WLAN
````

***

# 4. Container-Architektur mit Podman

## Container

```text
schoolprint-frontend
schoolprint-backend
schoolprint-postgres
schoolprint-slicer
schoolprint-updater
```

## Empfehlung

Für den MVP können Backend und Slicer auch in einem Container laufen. Langfristig ist ein separater Slicer-Worker sinnvoll.

Podman Compose kann Compose-Workloads über externe Compose-Provider wie `podman-compose` ausführen. <https://docs.podman.io/en/latest/markdown/podman-compose.1.html>

## Volumes

```text
/var/lib/schoolprint/uploads
/var/lib/schoolprint/sliced
/var/lib/schoolprint/previews
/var/lib/schoolprint/postgres
/var/lib/schoolprint/backups
```

## Netzwerk

```text
schoolprint-net
```

Optional:

* Raspberry Pi kann als WLAN Access Point betrieben werden.
* Der Bambu A1 Mini verbindet sich direkt mit diesem lokalen WLAN.
* Die Tablets verbinden sich ebenfalls mit diesem WLAN oder dem Schulnetz.

***

# 5. MVP-Funktionsumfang

## Enthalten im MVP

### User

* Login
* STL-Datei hochladen
* Titel/Projektname eingeben
* Optional: Klasse auswählen oder anzeigen
* Eigene Uploads sehen
* Status sehen:
  * Eingereicht
  * Abgelehnt
  * Freigegeben
  * In Warteschlange
  * Druckbereit
  * Druckend
  * Fertig
  * Fehler
  * Gelöscht/Abgelaufen
* Warteschlangenposition sehen
* Gedruckt-am-Datum sehen

### Admin/Lehrer

* Login
* Userkonten anlegen
* Admin-Konten anlegen
* Passwörter setzen/zurücksetzen
* Druckaufträge prüfen
* Druckaufträge freigeben
* Freigabe zurücknehmen
* Druckauftrag ablehnen
* Queue sortieren
* Druck manuell starten
* Druck pausieren/abbrechen, sofern Treiber unterstützt
* Druckerstatus sehen
* Systemstatus sehen
* Retention konfigurieren
* Update prüfen
* Update installieren

### System

* Lokale Dateispeicherung
* Datenbank-Metadaten
* Automatisches Löschen nach Retention
* Bambu A1 Mini als erster Druckertreiber
* Mehrdrucker-Datenmodell von Anfang an
* Initiales Setup mit erstem Admin

***

# 6. Bewusst nicht im MVP

Diese Dinge würde ich **nicht** in Version 0.1 bauen:

* Kein OctoPrint als Kernabhängigkeit
* Kein Cloud-Sync
* Keine externe Benutzerverwaltung/LDAP/Entra ID
* Kein komplexes Klassenbuch
* Keine automatische Druckerzuweisung
* Kein automatischer Druckstart ohne Lehrer
* Kein Zahlungs-/Filament-Kontingent
* Keine KI-Fehlererkennung
* Kein vollständiger Slicer-Editor im Browser
* Kein Mobile-Native-App

***

# 7. Projektstruktur

```text
schoolprint/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── printer_drivers/
│   │   ├── slicer/
│   │   ├── workers/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
│
├── deploy/
│   ├── compose.yaml
│   ├── systemd/
│   └── podman/
│
├── docs/
│   ├── architecture.md
│   ├── setup-raspberry-pi.md
│   ├── bambu-a1-mini.md
│   └── security.md
│
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   └── install.sh
│
├── .github/
│   └── workflows/
│
├── README.md
├── LICENSE
└── SECURITY.md
```

***

# 8. Datenmodell

## User

```text
users
-----
id
username
display_name
password_hash
role
class_name
is_active
created_at
updated_at
last_login_at
```

Rollen:

```text
ADMIN
USER
```

Für den MVP reicht ein geteilter Admin-Lehreraccount, aber das Modell sollte mehrere Admins unterstützen.

***

## Printer

```text
printers
--------
id
name
driver_type
host
port
serial_number
access_code_encrypted
is_active
location
created_at
updated_at
```

`driver_type`:

```text
BAMBU_LAN
OCTOPRINT
MOONRAKER
DUMMY
```

Für Version 0.1 wird nur `BAMBU_LAN` produktiv umgesetzt.

***

## UploadedFile

```text
uploaded_files
--------------
id
owner_id
original_filename
stored_filename
storage_path
content_type
file_size_bytes
sha256
created_at
expires_at
deleted_at
```

Wichtig: Ich würde die Datei **nicht als BLOB in PostgreSQL speichern**, sondern lokal im Dateisystem. In der DB liegen Pfad, Hash, Größe und Metadaten. Das erfüllt dein Ziel „alles lokal auf dem Raspberry“, bleibt aber deutlich robuster und einfacher zu sichern.

***

## PrintJob

```text
print_jobs
----------
id
owner_id
uploaded_file_id
printer_id
title
status
queue_position
teacher_note
student_note
estimated_print_time_seconds
estimated_filament_grams
created_at
approved_at
queued_at
started_at
finished_at
rejected_at
failed_at
expires_at
```

Status:

```text
SUBMITTED
REJECTED
APPROVED
QUEUED
READY_TO_PRINT
SLICING
SLICED
PRINTING
PAUSED
FINISHED
FAILED
CANCELLED
EXPIRED
DELETED
```

***

## SlicedArtifact

```text
sliced_artifacts
----------------
id
print_job_id
file_path
artifact_type
slicer_name
slicer_version
profile_name
created_at
```

`artifact_type`:

```text
GCODE_3MF
GCODE
PREVIEW
METADATA_JSON
```

Für Bambu ist `.gcode.3mf` als Zielartefakt sinnvoll, da Bambu-Workflows typischerweise 3MF/G-Code-Container nutzen. OrcaSlicer kann über CLI Workflows zum Export von 3MF/G-Code-Artefakten genutzt werden. <https://github.com/OrcaSlicer/OrcaSlicer/discussions/8593>

***

## AuditLog

```text
audit_logs
----------
id
actor_id
action
entity_type
entity_id
metadata_json
created_at
```

Beispiele:

```text
USER_CREATED
PASSWORD_RESET
JOB_APPROVED
JOB_REJECTED
QUEUE_REORDERED
PRINT_STARTED
PRINT_CANCELLED
RETENTION_DELETED
UPDATE_STARTED
```

***

## SystemSetting

```text
system_settings
---------------
key
value
updated_at
```

Beispiele:

```text
retention_days_finished = 90
max_upload_size_mb = 50
allowed_file_extensions = stl
default_printer_id = ...
school_name = ...
update_channel = stable
```

***

# 9. Backend-Module

## 9.1 Auth-Modul

Aufgaben:

* Login
* Logout
* Session/JWT
* Passwort-Hashing
* Rollenprüfung
* Initialer Admin-Bootstrap

Empfehlung:

* Argon2 oder bcrypt für Passwort-Hashing
* HTTP-only Cookie Session oder JWT im HTTP-only Cookie
* Keine Tokens im LocalStorage

API:

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
POST /api/auth/change-password
```

***

## 9.2 User-Management

Nur Admin.

API:

```text
GET    /api/admin/users
POST   /api/admin/users
GET    /api/admin/users/{id}
PATCH  /api/admin/users/{id}
POST   /api/admin/users/{id}/reset-password
POST   /api/admin/users/{id}/disable
POST   /api/admin/users/{id}/enable
```

***

## 9.3 Upload-Service

Aufgaben:

* Datei entgegennehmen
* Dateityp prüfen
* Größe prüfen
* SHA-256 bilden
* Lokal speichern
* DB-Eintrag erzeugen
* PrintJob mit Status `SUBMITTED` erzeugen

API:

```text
POST /api/user/uploads
GET  /api/user/jobs
GET  /api/user/jobs/{id}
```

Validierungen:

* Nur `.stl`
* Max-Upload-Größe konfigurierbar
* Dateiname normalisieren
* Speicherung nicht unter Originalnamen, sondern UUID-basiert
* MIME-Type nicht blind vertrauen
* Optional: STL grob parsen, um kaputte Dateien früh abzulehnen

***

## 9.4 PrintJob-Service

Admin-Funktionen:

```text
GET  /api/admin/jobs
GET  /api/admin/jobs/{id}
POST /api/admin/jobs/{id}/approve
POST /api/admin/jobs/{id}/reject
POST /api/admin/jobs/{id}/unapprove
POST /api/admin/jobs/{id}/enqueue
POST /api/admin/jobs/{id}/remove-from-queue
```

Statusregeln:

```text
SUBMITTED -> APPROVED
SUBMITTED -> REJECTED
APPROVED -> QUEUED
QUEUED -> READY_TO_PRINT
READY_TO_PRINT -> PRINTING
PRINTING -> FINISHED
PRINTING -> FAILED
```

***

## 9.5 Queue-Service

Aufgaben:

* Queue pro Drucker
* Position berechnen
* Reihenfolge ändern
* Nur Admin darf umsortieren
* User sehen nur eigene Position

API:

```text
GET  /api/admin/queue
POST /api/admin/queue/reorder
POST /api/admin/queue/{job_id}/move-up
POST /api/admin/queue/{job_id}/move-down
```

Wichtig:

* Queue-Änderungen transaktional
* Race Conditions vermeiden
* Sperren oder optimistic locking für Reorder

***

## 9.6 Slicer-Service

Aufgaben:

* STL in OrcaSlicer geben
* Vordefinierte Profile verwenden
* Ergebnisartefakt speichern
* Druckzeit/Filamentmenge extrahieren, soweit möglich
* Fehler sauber in `FAILED` oder `SLICING_FAILED` überführen

Flow:

```text
APPROVED
  -> SLICING
  -> SLICED
  -> QUEUED
```

Oder für den MVP einfacher:

```text
Freigabe löst Slicing aus.
Nach erfolgreichem Slicing wird der Auftrag in die Queue aufgenommen.
```

OrcaSlicer sollte über feste Profile betrieben werden, nicht über frei editierbare User-/Lehrereinstellungen. OrcaSlicer unterstützt CLI-Optionen zum Laden von Settings und Filament-Profilen. <https://github.com/OrcaSlicer/OrcaSlicer/discussions/1603>, <https://printago.io/blog/orca-slicer-cli-reference>

***

## 9.7 Printer Driver Interface

Zentrales Interface:

```text
PrinterDriver
-------------
get_status()
upload_artifact()
start_print()
pause_print()
resume_print()
cancel_print()
get_temperatures()
get_progress()
```

Implementierungen:

```text
BambuLanDriver
DummyDriver
```

Später:

```text
OctoPrintDriver
MoonrakerDriver
PrusaConnectDriver
```

Für den MVP sollte `DummyDriver` Teil des Projekts sein, damit Frontend, Queue und Tests ohne echten Drucker laufen.

***

## 9.8 BambuLanDriver

Aufgaben:

* Verbindung zum A1 Mini im LAN
* Status abrufen
* Druckauftrag übertragen
* Druck starten
* Fortschritt lesen
* Fehlerzustände melden

Technische Grundlage:

* Bambu LAN Mode ermöglicht lokale Kommunikation ohne Internet. <https://wiki.bambulab.com/en/knowledge-sharing/enable-lan-mode>
* Developer Mode öffnet bei A-Series-Geräten lokale Steuerungsmöglichkeiten wie MQTT und FTP. <https://wiki.bambulab.com/en/knowledge-sharing/enable-developer-mode>
* Community-Dokumentationen beschreiben lokale MQTT-Verbindungen gegen den Drucker mit IP, Port `8883`, Username `bblp` und Access Code. <https://github.com/Doridian/OpenBambuAPI/blob/main/mqtt.md>

MVP-Umfang:

```text
get_status()
upload_artifact()
start_print()
cancel_print()
```

Nicht zwingend im MVP:

```text
camera()
ams_status()
firmware_update()
calibration()
```

***

## 9.9 Retention-Service

Aufgaben:

* Täglich alternde Dateien erkennen
* Fertige/abgelehnte/fehlgeschlagene Jobs nach konfigurierter Zeit löschen
* Datei vom Dateisystem entfernen
* DB-Einträge soft-deleten oder anonymisieren
* AuditLog schreiben

Regeln:

```text
FINISHED älter als retention_days_finished -> Datei löschen
REJECTED älter als retention_days_rejected -> Datei löschen
FAILED älter als retention_days_failed -> Datei löschen
```

Empfehlung:

* Metadaten zunächst behalten
* Datei löschen
* Username optional nach längerer Zeit anonymisieren

***

## 9.10 Update-Service

Aufgaben:

* GitHub Releases prüfen
* Aktuelle Version mit neuester Release-Version vergleichen
* Update im UI anzeigen
* Admin klickt „Update installieren“
* Updater zieht neue Container-Images
* Compose/Podman Stack wird neu gestartet

Wichtige Sicherheitsentscheidung:

Der Backend-Container sollte **nicht unkontrolliert Root-Zugriff auf den Host** bekommen.

Empfohlene Architektur:

```text
Backend
  -> schreibt UpdateRequest in DB
  -> ruft lokalen Updater-Service auf

Updater-Service
  -> hat minimal nötige Rechte
  -> podman pull
  -> podman compose up -d
```

Podman Compose ist als Compose-kompatibles Werkzeug für Podman-Setups vorgesehen. <https://docs.podman.io/en/latest/markdown/podman-compose.1.html>, <https://github.com/containers/podman-compose>

***

# 10. Frontend-Plan

## 10.1 Routing

```text
/login

/user
/user/jobs
/user/jobs/:id
/user/upload

/admin
/admin/users
/admin/jobs
/admin/queue
/admin/printers
/admin/settings
/admin/system
/admin/updates
```

***

## 10.2 Useransicht

### Dashboard

Zeigt:

* Anzahl eigener Uploads
* Aktive Druckaufträge
* Fertige Drucke
* Nächster Auftrag in Queue

### Upload-Seite

Felder:

```text
Titel
Datei auswählen
Kommentar optional
Absenden
```

Nach Upload:

```text
Dein Modell wurde eingereicht.
Status: Wartet auf Freigabe.
```

### Meine Druckaufträge

Tabelle/Karten:

```text
Titel
Datei
Status
Position
Eingereicht am
Freigegeben am
Gedruckt am
```

***

## 10.3 Adminansicht

### Admin-Dashboard

Kacheln:

```text
Offene Freigaben
Queue-Länge
Aktive Drucke
Drucker online/offline
Speicherverbrauch
```

### Nutzerverwaltung

Funktionen:

* Nutzer anlegen
* Rolle setzen
* Klasse setzen
* Passwort setzen
* Passwort zurücksetzen
* Nutzer deaktivieren

### Druckanfragen

Tabelle:

```text
Titel
User
Klasse
Datei
Eingereicht am
Status
Aktionen
```

Aktionen:

```text
Ansehen
Freigeben
Ablehnen
Freigabe zurücknehmen
```

### Queue

Drag-and-Drop-Liste:

```text
1. Haus - Max - Drucker A
2. Roboter - Anna - Drucker A
3. Schlüsselanhänger - Tim - Drucker B
```

Aktionen:

```text
Nach oben
Nach unten
Drucker ändern
Aus Queue entfernen
Druck starten
```

### Druckeransicht

Pro Drucker:

```text
Name
Status
IP
Temperaturen
Fortschritt
Aktueller Job
Letzte Aktualisierung
```

Aktionen:

```text
Status aktualisieren
Druck starten
Pause
Fortsetzen
Abbrechen
```

### Systemdaten

Anzeigen:

```text
CPU-Auslastung
RAM
Datenträger
Upload-Speicher
Sliced-Artefakte
Container-Version
Backend-Version
Frontend-Version
```

***

# 11. Slicing-Workflow

## Empfohlener MVP-Workflow

```text
1. User lädt STL hoch
2. Job bekommt Status SUBMITTED
3. Lehrer prüft Modell
4. Lehrer klickt Freigeben
5. Backend startet Slicing
6. OrcaSlicer erzeugt .gcode.3mf
7. SlicedArtifact wird gespeichert
8. Job kommt in Queue
9. Lehrer entfernt vorherigen Druck von Druckplatte
10. Lehrer klickt "Druck starten"
11. Backend sendet Artefakt an Drucker
12. Backend startet Druck
13. Status wird regelmäßig aktualisiert
14. Nach Abschluss: FINISHED + finished_at
```

## Warum Slicing bei Freigabe?

Vorteile:

* Lehrer sieht vor dem Queueing mögliche Fehler
* Druckzeit/Filament kann vor Druckstart angezeigt werden
* Queue enthält nur technisch vorbereitete Jobs

***

# 12. Bambu-A1-Mini-Setup für MVP

## Voraussetzungen

Am Drucker:

```text
LAN Only Mode aktivieren
Developer Mode aktivieren
Access Code notieren
Statische IP vergeben
```

Bambu beschreibt LAN Mode als lokale Betriebsart, bei der der Drucker im LAN mit dem Slicer kommunizieren kann, ohne dass ein Internetzugang erforderlich ist. <https://wiki.bambulab.com/en/knowledge-sharing/enable-lan-mode>

## In SchoolPrint

Admin trägt ein:

```text
Name: A1 Mini Raum 101
Host: 192.168.50.20
Seriennummer / Device-ID
Access Code
Treiber: Bambu LAN
```

Access Code:

* verschlüsselt speichern
* nie im Frontend anzeigen
* nur überschreibbar machen

***

# 13. API-Design

## Public/Auth

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

## User

```text
POST /api/user/uploads
GET  /api/user/jobs
GET  /api/user/jobs/{job_id}
```

## Admin Users

```text
GET   /api/admin/users
POST  /api/admin/users
PATCH /api/admin/users/{user_id}
POST  /api/admin/users/{user_id}/reset-password
```

## Admin Jobs

```text
GET  /api/admin/jobs
GET  /api/admin/jobs/{job_id}
POST /api/admin/jobs/{job_id}/approve
POST /api/admin/jobs/{job_id}/reject
POST /api/admin/jobs/{job_id}/unapprove
POST /api/admin/jobs/{job_id}/enqueue
```

## Admin Queue

```text
GET  /api/admin/queue
POST /api/admin/queue/reorder
POST /api/admin/queue/{job_id}/start
POST /api/admin/queue/{job_id}/remove
```

## Printers

```text
GET  /api/admin/printers
POST /api/admin/printers
GET  /api/admin/printers/{printer_id}
PATCH /api/admin/printers/{printer_id}
GET  /api/admin/printers/{printer_id}/status
POST /api/admin/printers/{printer_id}/test-connection
```

## System

```text
GET  /api/admin/system/status
GET  /api/admin/system/storage
GET  /api/admin/system/version
POST /api/admin/system/retention/run
```

## Updates

```text
GET  /api/admin/updates/check
POST /api/admin/updates/install
GET  /api/admin/updates/status
```

***

# 14. Rollen- und Rechtekonzept

## USER darf

```text
Eigene Jobs sehen
Eigene STL hochladen
Eigene Jobdetails ansehen
```

## USER darf nicht

```text
Druck starten
Andere User sehen
Queue verändern
Dateien anderer User herunterladen
Systemdaten sehen
Drucker konfigurieren
```

## ADMIN darf

```text
Alle Jobs sehen
Alle Nutzer verwalten
Jobs freigeben/ablehnen
Queue ändern
Druck starten
Drucker verwalten
Systemdaten sehen
Updates starten
Retention konfigurieren
```

***

# 15. Sicherheit

## Mindestanforderungen

* Passwort-Hashing mit Argon2 oder bcrypt
* CSRF-Schutz bei Cookie-basierter Auth
* Rate-Limit für Login
* Upload-Limit
* Dateiendung und Dateiinhalt prüfen
* Keine Original-Dateinamen als Speicherpfade verwenden
* Keine Shell-Kommandos mit ungeprüften Dateinamen
* Slicer-Ausführung mit Timeout
* Slicer in isoliertem Worker/Container
* Access Codes verschlüsselt speichern
* AuditLog für Admin-Aktionen

## Besonders wichtig beim Slicer

Der Slicer verarbeitet von Usern hochgeladene Dateien. Deshalb:

```text
Input-Dateien in isoliertes Arbeitsverzeichnis
Timeout setzen
Maximale Dateigröße setzen
Keine Pfade aus Userinput übernehmen
Subprocess ohne shell=True starten
```

***

# 16. Implementierungsphasen

## Phase 0: Repository-Bootstrap

Ziel: Projekt startfähig machen.

Aufgaben:

1. GitHub Repo erstellen
2. Lizenz wählen, z. B. AGPLv3 oder GPLv3, wenn Cloud-/SaaS-Forks zurückfließen sollen
3. README mit Projektziel
4. Backend-Projektstruktur erstellen
5. Frontend-Projektstruktur erstellen
6. Compose/Podman-Grundsetup erstellen
7. PostgreSQL-Container integrieren
8. CI mit Lint/Test vorbereiten

Ergebnis:

```text
podman compose up
```

startet Backend, Frontend und PostgreSQL.

***

## Phase 1: Auth und Benutzerverwaltung

Ziel: Login und Rollen funktionieren.

Aufgaben:

1. User-Modell erstellen
2. Alembic-Migration erstellen
3. Passwort-Hashing integrieren
4. Login-Endpunkte bauen
5. Rollenprüfung bauen
6. Initialen Admin-Bootstrap implementieren
7. Admin-User-CRUD bauen
8. Frontend-Login bauen
9. Admin-Nutzerverwaltung bauen

Verifikation:

* Admin kann sich einloggen
* Admin kann User anlegen
* User kann sich einloggen
* User sieht keine Admin-Routen
* Passwort-Reset funktioniert

***

## Phase 2: Upload und Userbereich

Ziel: User können STL-Dateien hochladen und eigene Jobs sehen.

Aufgaben:

1. UploadedFile-Modell erstellen
2. PrintJob-Modell erstellen
3. Lokalen Upload-Speicher konfigurieren
4. Upload-API bauen
5. Datei-Validierung bauen
6. User-Dashboard bauen
7. User-Jobliste bauen
8. Jobdetails bauen

Verifikation:

* User lädt `.stl` hoch
* Datei liegt lokal im Upload-Verzeichnis
* DB enthält Metadaten
* User sieht nur eigene Jobs
* Admin sieht alle Jobs

***

## Phase 3: Admin-Freigabeprozess

Ziel: Lehrer können Drucke prüfen, freigeben und ablehnen.

Aufgaben:

1. Admin-Jobliste bauen
2. Approve/Reject-Endpunkte bauen
3. Statusmaschine sauber implementieren
4. AuditLog integrieren
5. Admin-Kommentar hinzufügen
6. Frontend-Aktionen bauen

Verifikation:

* Job startet als `SUBMITTED`
* Admin kann freigeben
* Admin kann ablehnen
* User sieht neuen Status
* AuditLog enthält Aktion

***

## Phase 4: Queue-Management

Ziel: Lehrer können Warteschlange verwalten.

Aufgaben:

1. Queue-Position zum Modell hinzufügen
2. Queue-Service implementieren
3. Enqueue-Logik bauen
4. Reorder-API bauen
5. Drag-and-Drop oder Up/Down im Frontend bauen
6. Queue pro Drucker vorbereiten

Verifikation:

* Freigegebene Jobs können in Queue
* Positionen sind eindeutig
* Admin kann Reihenfolge ändern
* User sieht eigene Position
* Reorder bleibt nach Neustart erhalten

***

## Phase 5: OrcaSlicer-Integration

Ziel: Freigegebene Jobs werden lokal gesliced.

Aufgaben:

1. Slicer-Konfigurationsverzeichnis definieren
2. Bambu-A1-Mini-Profil hinterlegen
3. Filamentprofil PLA hinterlegen
4. Slicer-Service bauen
5. Subprocess-Ausführung mit Timeout bauen
6. SlicedArtifact-Modell erstellen
7. Slicing-Logs speichern
8. Fehlerbehandlung implementieren

Verifikation:

* STL wird zu `.gcode.3mf` verarbeitet
* Artefakt liegt lokal
* Fehlerhafte STL erzeugt sauberen Fehlerstatus
* Druckzeit/Filament wird, wenn extrahierbar, gespeichert

***

## Phase 6: Printer-Abstraktion und DummyDriver

Ziel: Druckerlogik ist abstrahiert und testbar.

Aufgaben:

1. `PrinterDriver` Interface definieren
2. `DummyDriver` implementieren
3. Printer-Modell erstellen
4. Printer-CRUD bauen
5. Druckerstatus-API bauen
6. Admin-Druckeransicht bauen
7. Start-Print-Flow gegen DummyDriver bauen

Verifikation:

* Admin kann Drucker anlegen
* Dummy-Drucker meldet Status
* Job kann mit DummyDriver „gedruckt“ werden
* Status wechselt bis `FINISHED`

***

## Phase 7: BambuLanDriver MVP

Ziel: Bambu A1 Mini lokal steuern.

Aufgaben:

1. Bambu-Drucker-Konfiguration speichern
2. Access Code verschlüsselt speichern
3. Verbindungstest bauen
4. MQTT-Status abrufen
5. Artefakt zum Drucker übertragen
6. Druckstart implementieren
7. Fortschritt pollend oder eventbasiert aktualisieren
8. Fehlerzustände mappen

Verifikation:

* Verbindungstest erfolgreich
* Druckerstatus wird angezeigt
* Dateiübertragung funktioniert
* Manueller Start aus WebUI startet Druck
* Fortschritt wird im Adminbereich angezeigt
* Abschluss wird erkannt

***

## Phase 8: Retention und Aufräumen

Ziel: Dateien werden nach Regeln gelöscht.

Aufgaben:

1. Retention-Settings in SystemSetting ergänzen
2. Retention-Worker bauen
3. Manuelles Ausführen im Adminbereich ermöglichen
4. Täglichen Job konfigurieren
5. AuditLog schreiben
6. Speicherübersicht bauen

Verifikation:

* Testjob mit alter Datei wird gelöscht
* DB bleibt konsistent
* User sieht abgelaufenen Status
* Admin sieht Löschprotokoll

***

## Phase 9: Systemstatus und Updates

Ziel: Admin sieht Systemdaten und kann Updates starten.

Aufgaben:

1. Version in Backend und Frontend expose’n
2. GitHub Release Check bauen
3. Update-Status-Modell bauen
4. Updater-Service bauen
5. Podman Pull/Restart implementieren
6. Admin-Update-Seite bauen
7. Fehler- und Rollback-Hinweise anzeigen

Verifikation:

* Aktuelle Version wird angezeigt
* Update-Check funktioniert
* Update-Button startet Updater
* Update-Log ist sichtbar
* Fehlgeschlagenes Update wird sauber gemeldet

***

# 17. Teststrategie

## Backend Tests

* Unit Tests für Statusmaschine
* Unit Tests für Queue-Reorder
* Unit Tests für Retention
* Unit Tests für Rollenprüfung
* Integration Tests für Upload
* Integration Tests für Admin-Freigabe
* Integration Tests für DummyDriver
* Tests für Slicer-Service mit kleiner Beispiel-STL

## Frontend Tests

* Login-Seite rendert
* User-Upload funktioniert gegen Mock API
* User sieht eigene Jobs
* Admin sieht Jobliste
* Queue-Reorder UI funktioniert
* Admin kann Druck starten

## End-to-End Tests

MVP-E2E mit DummyDriver:

```text
Admin erstellt User
User lädt STL hoch
Admin gibt frei
Slicer erzeugt Artefakt
Admin startet Druck
DummyDriver beendet Druck
User sieht FINISHED
```

## Hardware-Test mit Bambu A1 Mini

```text
Bambu im LAN Mode
Developer Mode aktiv
Verbindungstest
Statusabruf
Upload kleines Testmodell
Manueller Druckstart
Fortschritt prüfen
Abschluss prüfen
```

***

# 18. MVP-Reihenfolge für schnelle Ergebnisse

Wenn du schnell einen nutzbaren Prototypen möchtest, würde ich so vorgehen:

1. Backend + DB + Auth
2. Userupload
3. Adminfreigabe
4. Queue
5. DummyDriver
6. OrcaSlicer
7. BambuLanDriver
8. Retention
9. Updates

Warum DummyDriver vor Bambu?

Damit du den kompletten Schulworkflow bauen und testen kannst, bevor du dich mit Bambu-Protokolldetails beschäftigst.

***

# 19. GitHub Issues für den MVP

## Milestone 0.1.0 MVP

### Backend

* Projektstruktur FastAPI anlegen
* PostgreSQL anbinden
* Alembic einrichten
* User-Modell
* Auth
* Rollenprüfung
* Upload-Modell
* PrintJob-Modell
* Printer-Modell
* Queue-Service
* Slicer-Service
* DummyDriver
* BambuLanDriver MVP
* Retention-Service
* Update-Service
* AuditLog

### Frontend

* Layout/Shell
* Login
* Userdashboard
* Uploadseite
* User-Jobliste
* Admin-Dashboard
* User-Management
* Job-Freigabeansicht
* Queue-Ansicht
* Druckeransicht
* Systemeinstellungen
* Update-Seite

### Deployment

* Podman Compose
* Volumes
* Environment-Konfiguration
* Raspberry-Pi-Installationsskript
* Backup-Skript
* Restore-Skript

### Dokumentation

* README
* Installationsanleitung
* Bambu-A1-Mini-Setup
* Sicherheitsmodell
* Admin-Handbuch
* User-Kurzanleitung

***

# 20. Wichtige Architekturentscheidungen

## Entscheidung 1: Kein OctoPrint im Kern

OctoPrint wird nicht Kernbestandteil des MVP. Stattdessen bekommt das System eigene Druckertreiber.

Begründung:

* Ziel ist vollständige Steuerung über deine WebUI
* OctoPrint wäre eine zusätzliche Ebene
* Bambu A1 Mini passt nicht sauber zum klassischen OctoPrint-USB-Modell

## Entscheidung 2: Bambu A1 Mini als Referenzdrucker

Der erste echte Treiber wird `BambuLanDriver`.

Begründung:

* Der A1 Mini ist für Grundschulen attraktiv
* LAN Mode und Developer Mode erlauben lokale Kommunikation
* Kein Cloud-Zwang im Zielbetrieb

## Entscheidung 3: OrcaSlicer als interner Slicer

Der Benutzer sieht OrcaSlicer nicht.

Begründung:

* Etablierte Profile für Bambu
* CLI-Nutzung für Automatisierung möglich
* Passt gut zu lokalem Workflow

## Entscheidung 4: Dateien lokal, Metadaten in DB

Nicht als PostgreSQL-BLOB speichern.

Begründung:

* Einfachere Backups
* Einfachere Retention
* Weniger DB-Bloat
* Trotzdem vollständig lokal auf dem Raspberry Pi

## Entscheidung 5: Druckstart immer manuell

Auch wenn Queue und Slicing automatisch laufen, startet der eigentliche Druck nur nach Lehrer-Klick.

Begründung:

* Druckplatte muss frei sein
* Schule braucht Aufsicht
* Verhindert gefährliche oder fehlerhafte Automatisierung

***

# 21. Definition of Done für MVP

Der MVP ist fertig, wenn:

1. Admin kann User anlegen.
2. User kann sich einloggen.
3. User kann STL-Datei hochladen.
4. User sieht eigenen Auftrag und Status.
5. Admin sieht offene Druckanfragen.
6. Admin kann Auftrag freigeben oder ablehnen.
7. Freigegebener Auftrag wird gesliced.
8. Auftrag erscheint in Queue.
9. Admin kann Queue sortieren.
10. Admin kann Druck manuell auf Bambu A1 Mini starten.
11. Admin sieht Druckerstatus und Druckfortschritt.
12. User sieht „fertig gedruckt am Datum“.
13. Alte Dateien werden nach Retention gelöscht.
14. System läuft lokal per Podman auf Raspberry Pi.
15. Update-Check gegen GitHub Releases funktioniert.
16. Installation ist dokumentiert.

***
