# imPress engineering documentation

imPress is a classroom-response system with a FastAPI service, web clients and ESP32 firmware. This site is the searchable, versioned reference for operating, integrating and extending the system.

```{toctree}
:maxdepth: 2
:caption: Start here

README
graph/index
install/platforms
install/flashing
user-guide/README
user-guide/administrator
user-guide/teacher
user-guide/glossary
user-guide/faq
architecture/overview
guides/development-setup
guides/deployment
guides/troubleshooting
guides/graphify
deployment/README
deployment/container
```

```{toctree}
:maxdepth: 2
:caption: Architecture and design

architecture/backend
architecture/firmware
architecture/data-flows
design/protocols
design/mesh
design/mesh-authentication
design/security-model
design/data-integrity
design/gpc
design/trusted-boot
design/integrity-protection
design/traffic-monitor
design/ui-design
design/authorization
design/scheduling
design/student-ota
design/decisions
```

```{toctree}
:maxdepth: 2
:caption: APIs and operations

api/rest-api
api/websocket-api
api/device-api
guides/configuration
guides/csv-imports
guides/test-mode
guides/accounts-and-onboarding
guides/personalization
guides/backups
guides/console
guides/launch-flags
guides/production-hardening
guides/ota-updates
guides/releases
guides/testing
```

```{toctree}
:maxdepth: 2
:caption: Privacy and compliance

compliance/README
compliance/data-inventory
compliance/privacy-notice-template
compliance/retention-schedule
compliance/dsar-runbook
compliance/incident-response
compliance/control-mapping
compliance/risk-register
```

```{toctree}
:maxdepth: 2
:caption: Hardware, firmware and reference

hardware/CLASSROOM_NODE_REQUIREMENTS
hardware/DEVICE_COMPATIBILITY
firmware/OTA_ARCHITECTURE
firmware/FIRMWARE_VERSIONING
firmware/RECOVERY_PROCEDURE
reference/placeholders
reference/data-model
reference/hardware
reference/known-issues
reference/flags
reference/errors
reference/changelog-v2.1
reference/changelog-v2
```

```{toctree}
:maxdepth: 2
:caption: Verification and engineering record

testing/TEST_STRATEGY
testing/HARDWARE_VALIDATION
engineering/DATABASE_MIGRATIONS
engineering/SECURITY_REVIEW
engineering/SYSTEM_AUDIT
engineering/PERMISSIONS_AND_OTA_REVIEW
engineering/V2.1_ENGINEERING_REPORT
engineering/V2_V3_COMPARISON
engineering/REFACTOR_ROADMAP
engineering/V2.2_PLAN
releases/v2.1
releases/v2.2
```

## Find what you need

Use the search box in the upper left to search every rendered guide. For code and component relationships, use the interactive [knowledge graph](graph/index.md). The deployed application also provides the same graph and a fast documentation search at `/graph`.
