# SchoolPrint

SchoolPrint is a local, school-friendly 3D-print management system designed
to run entirely on a Raspberry Pi. Students upload STL files, teachers
review and approve them, approved jobs are sliced automatically and queued,
and prints are always started manually from the web interface under
teacher supervision.

See [initial_prompt.md](initial_prompt.md) for the full original design
document (in German) that this implementation follows.

## Project goals (MVP)

- Login with `ADMIN` (teacher) and `USER` (student) roles
- Users upload `.stl` files and track their own print jobs
- Teachers review, approve, or reject submissions
- Approved jobs are sliced with OrcaSlicer and placed in a print queue
- Prints are always started manually, never automatically
- A Bambu Lab A1 Mini is the first supported printer, driven natively over
  the local network (no OctoPrint, no cloud)
- Everything — files, database, backups — stays local on the Raspberry Pi
- The whole stack is deployed with Podman Compose

## Repository layout

```text
backend/    FastAPI application (Python), SQLAlchemy + Alembic, tests
frontend/   React + TypeScript + shadcn/ui web app
deploy/     Podman Compose stack, systemd unit, Podman-specific config
docs/       Architecture, setup, and security documentation
scripts/    Install/backup/restore helper scripts
```

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then edit SCHOOLPRINT_DATABASE_URL etc.
alembic upgrade head
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000`; interactive docs are at
`http://localhost:8000/docs`. On first startup, if no users exist yet, an
initial `admin` account is bootstrapped and its generated password is
printed to the backend logs.

Run tests with:

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies `/api/*`
requests to the backend at `http://localhost:8000`.

Run component tests and lint/build with:

```bash
npm run test
npm run lint
npm run build
```

## Deployment (Raspberry Pi / Podman)

```bash
./scripts/install.sh
cd /opt/schoolprint/deploy
podman-compose -f compose.yaml --env-file .env up -d
```

See [docs/setup-raspberry-pi.md](docs/setup-raspberry-pi.md) for the full
installation guide and [docs/bambu-a1-mini.md](docs/bambu-a1-mini.md) for
printer-specific setup.

## Security

See [SECURITY.md](SECURITY.md) and [docs/security.md](docs/security.md).

## License

See [LICENSE](LICENSE).
