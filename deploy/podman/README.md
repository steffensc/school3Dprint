# Podman-specific configuration

This directory is reserved for Podman-specific assets that don't fit into
the generic `compose.yaml` (for example rootless Podman Quadlet unit files,
or `containers.conf` overrides for the Raspberry Pi host).

Nothing is required here for the MVP; `deploy/compose.yaml` plus
`deploy/systemd/schoolprint.service` fully describe the deployment.
