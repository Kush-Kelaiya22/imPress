# Glossary

| Term | Meaning in imPress |
|---|---|
| **Backend / server** | FastAPI application that serves the browser UI and API, stores classroom data, and coordinates connected devices. |
| **Course** | Catalog record for a subject, identified by a course code. A course can have multiple classroom sections. |
| **Class / classroom / section** | A scheduled teaching group with a roster, teacher, course and optional physical room code. |
| **Classroom code** | The room label used to associate a gateway with the intended class during registration or administrator linking. |
| **Gateway (C6)** | ESP32-C6 device that connects the room to the backend and relays messages between the backend and hub. |
| **Hub (S3)** | ESP32-S3 device that communicates with the gateway and coordinates student modules in the room. |
| **Student module** | Student-facing ESP32 device. It sends responses over ESP-NOW and does not join the classroom Wi-Fi network. |
| **ESP-NOW mesh** | Local radio links between student modules and the hub; relays can extend reach. It is separate from the server Wi-Fi connection. |
| **Quiz** | A set of questions and choices with a correct answer, run manually or with a timer. |
| **Poll** | A question with answer options and vote totals; it has no quiz answer key. |
| **OTA (over-the-air) update** | Firmware delivery over the network to supported hubs and gateways. Student modules are currently updated over serial. |
| **Canary** | First small group in a staged firmware rollout. Later batches proceed only according to rollout policy. |
| **Qualification** | Server-side checks of an uploaded firmware artifact before an administrator can approve or offer it. Qualification is not a substitute for physical hardware testing. |
| **Rollback** | Bootloader or operator recovery to a known-good firmware image after an unsuccessful update. |
| **NVS** | ESP-IDF nonvolatile key/value storage used for device configuration such as Wi-Fi, backend address and device credentials. |
