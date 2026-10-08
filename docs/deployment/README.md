# Deployment

Putting imPress into classrooms. The pages already exist as guides; this folder indexes them so that nothing is written twice.

| Topic | Page |
|---|---|
| Installation: server, systemd, nginx, TLS, first admin, go-live checklist, upgrading | [Deployment guide](../guides/deployment.md) |
| Configuration: every backend setting, every gateway, hub and student Kconfig and NVS key | [Configuration guide](../guides/configuration.md) |
| Troubleshooting: resets, connectivity, mesh, backend data, OTA | [Troubleshooting guide](../guides/troubleshooting.md), [OTA troubleshooting](../guides/ota-updates.md#troubleshooting-ota) |
| Choosing hardware for a room | [Classroom node requirements](../hardware/CLASSROOM_NODE_REQUIREMENTS.md) |
| Recovering from a failed update or upgrade | [Recovery procedure](../firmware/RECOVERY_PROCEDURE.md) |

Quick path: `scripts/install.sh`, then `scripts/start.sh`, then `scripts/smoke_test.py` (see the [deployment guide](../guides/deployment.md#1-server)).
