# First 30 minutes with imPress

This path takes a new operator from an empty installation to a classroom that can run a practice question. It assumes you have permission to administer the installation and that the service is reachable. For a shared or real classroom, finish TLS and the [go-live checklist](../guides/deployment.md#4-go-live-checklist) first.

## 1. Install and sign in

Use [the platform installation guide](../install/platforms.md) or the [container guide](../deployment/container.md). Open the server URL in a browser and sign in as the initial `admin`. Change the initial password in **Settings** immediately. A classroom browser accessed from another computer must use HTTPS; `127.0.0.1` is the local-only exception.

Expected: **Admin**, **Courses**, **Students**, **Classrooms**, **Modules**, **Firmware**, **Users**, and **Activity** are available to an administrator. A teacher instead sees **My Classes**. If a page is missing, confirm you signed in with the expected role; do not share an administrator login as a workaround.

## 2. Create the teaching team and course

An administrator creates staff accounts in **Users** and course records in **Courses**. See the [administrator guide](administrator.md) for account lifecycle, roles and recovery. Then create a classroom section, assign its teacher, and enroll students; see [classrooms and rosters](administrator.md#classrooms-and-rosters).

Expected: the teacher signs in with their own account and sees the assigned class under **My Classes**. If they cannot see it, verify the class assignment and account status. A teacher should not be granted admin privileges just to run a quiz.

## 3. Connect the room

Configure and flash the gateway (C6), hub (S3), and student modules using the [per-room hardware steps](../guides/deployment.md#3-per-room-hardware). The hardware guide covers the network values, room linking, and first serial flash. In **Modules**, check the device's status and diagnostic reason. A student module is not a Wi-Fi client; it uses the room's ESP-NOW mesh through the hub/gateway.

Expected: the room's gateway and hub become online and are associated with the correct active class. If not, follow [gateway and hub first boot](../guides/troubleshooting.md#gateway-and-hub-first-boot). Do not test a production rollout on an unverified room.

## 4. Run a practice question

As the assigned teacher:

1. Open **My Classes**, choose the class, then **+ New Quiz**.
2. Enter a title and at least one question. Each question needs 2–4 options; prefix the correct option with `*` (for example, `*Mercury`).
3. Choose **Planned** if you want to review it before starting, or **Impromptu** if it should go live when created. Choose **Manual** to advance questions yourself, **Per-Question Timer** for a time limit per question, or a total timer where shown.
4. Select **Create Quiz**. For a planned quiz, return to the class and select **Start** when ready. For an active manual quiz, use **Next** to advance; use **Stop** to finish early.
5. Check the module display and answer count, then open **Results** after completion.

Expected: the current question and its options appear to connected student modules; answers update the live count and completed results become available. If modules do not receive a question, check the class link, mesh channel, and gateway/hub status before repeating the quiz.

## 5. Try a poll and finish

From the class, select **+ New Poll**, enter a question and 2–4 options, then choose **Live** (starts immediately) or **Planned** (start from the class page). End the poll when ready and open **Results**. A module offers four physical answer buttons; keep poll choices within that limit.

Use the [teacher guide](teacher.md) for detailed quiz, poll, class, and results steps. Use the [FAQ](faq.md) when a result differs and the [glossary](glossary.md) for project terminology.
