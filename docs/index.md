# imPress engineering documentation

imPress is a classroom-response system with a FastAPI service, web clients and ESP32 firmware. This site is the searchable, versioned reference for operating, integrating and extending the system.

```{toctree}
:maxdepth: 2
:caption: Start here

README
graph
architecture/overview
guides/development-setup
guides/deployment
guides/troubleshooting
guides/graphify
deployment/README
```

```{toctree}
:maxdepth: 2
:caption: Architecture and design

architecture/backend
architecture/firmware
architecture/data-flows
design/protocols
design/mesh
design/security-model
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
guides/ota-updates
guides/releases
guides/testing
```

```{toctree}
:maxdepth: 2
:caption: Hardware, firmware and reference

hardware/CLASSROOM_NODE_REQUIREMENTS
hardware/DEVICE_COMPATIBILITY
firmware/OTA_ARCHITECTURE
firmware/FIRMWARE_VERSIONING
firmware/RECOVERY_PROCEDURE
reference/data-model
reference/hardware
reference/known-issues
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
engineering/V2.1_ENGINEERING_REPORT
engineering/V2_V3_COMPARISON
releases/v2.1
```

## Find what you need

Use the search box in the upper left to search every rendered guide. For code and component relationships, use the interactive [knowledge graph](graph.md). The deployed application also provides the same graph and a fast documentation search at `/graph`.
