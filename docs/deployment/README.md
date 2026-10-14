# Deployment and operations

Choose the path that matches your role. For a new installation, begin with [first 30 minutes](../user-guide/README.md), then use the relevant platform and operator procedures below. Procedures distinguish a local smoke test from a production classroom deployment; a local server is not ready for remote staff use until TLS, network access, backups and device checks are complete.

| Audience / task | Guide |
|---|---|
| First-time installer choosing Windows, macOS or Linux | [Native installation by platform](../install/platforms.md) |
| Operator deploying the published amd64/arm64 container | [Container image](container.md) — ports, persistent `/data`, Compose, TLS, backups, upgrades and recovery |
| Operator installing from source, configuring TLS, service supervision or upgrading | [Deployment guide](../guides/deployment.md) |
| Administrator creating users, courses, classes and rosters | [Administrator guide](../user-guide/administrator.md) |
| Teacher running a quiz or poll | [Teacher guide](../user-guide/teacher.md) |
| Hardware builder configuring, building, flashing and enrolling devices | [Firmware flashing guide](../install/flashing.md), [configuration reference](../guides/configuration.md) |
| Diagnosing resets, connectivity, mesh, backend data or OTA | [Troubleshooting guide](../guides/troubleshooting.md), [OTA troubleshooting](../guides/ota-updates.md#troubleshooting-ota) |
| Choosing the number/type of nodes for a room | [Classroom node requirements](../hardware/CLASSROOM_NODE_REQUIREMENTS.md) |
| Recovering from an update or administrator access failure | [Firmware recovery](../firmware/RECOVERY_PROCEDURE.md), [administrator recovery](../guides/deployment.md#recovering-administrator-access) |

Quick local check: on Linux/macOS run `scripts/install.sh`, `scripts/start.sh`, then `scripts/smoke_test.py` (see the [server setup](../guides/deployment.md#1-server)). For Windows PowerShell use [platform-specific setup](../install/platforms.md#windows-powershell). For a real classroom, complete the deployment guide's [go-live checklist](../guides/deployment.md#4-go-live-checklist).
