# Build context is the repository root (see deploy/compose.yaml) so this
# image can include the shared scripts/updater-trigger.sh script.
FROM python:3.12-alpine

# podman-compose + podman CLI are the only privileged tools this image
# needs; the backend image never installs these (Section 20).
RUN apk add --no-cache podman podman-compose bash

WORKDIR /app
COPY deploy/updater/updater_service.py ./
COPY scripts/updater-trigger.sh /opt/schoolprint/scripts/updater-trigger.sh
RUN chmod +x /opt/schoolprint/scripts/updater-trigger.sh

ENV PORT=8090 \
    SCHOOLPRINT_UPDATER_SCRIPT=/opt/schoolprint/scripts/updater-trigger.sh \
    SCHOOLPRINT_COMPOSE_FILE=/deploy/compose.yaml

EXPOSE 8090

CMD ["python", "updater_service.py"]
