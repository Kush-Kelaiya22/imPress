# Administrator guide

Use a personal administrator account for routine work. The application checks permissions on the server; hiding a button in the browser is not a permission boundary. A `super_admin` can manage administrator accounts and installation-wide settings; an `admin` manages day-to-day teaching data and devices within the permissions the server grants.

## Users and account lifecycle

1. Open **Users** and choose **+ New User**.
2. Enter a unique username, full name, email address and a strong initial password. Choose **Teacher** for an instructor. Give **Admin** only to staff who need to administer courses, students, classrooms or devices.
3. Submit the form and ask the person to sign in with their own account and change the initial password in **Settings**.
4. Use the account's status/actions to deactivate an account when access should stop. Deactivation prevents future sign-in and revokes active sessions; preserve the account when its records must remain attached to classes or activity history.

Expected: the account appears with its role and active status. Duplicate usernames/emails, weak passwords and attempts to remove the last active super administrator are refused with an explanation. Do not put passwords in CSV files that are stored or shared after import. For CSV user import, follow the UI's required columns and its preview/validation result.

If every super administrator is unavailable, use the server-side [administrator recovery procedure](../guides/deployment.md#recovering-administrator-access). There is intentionally no public recovery API.

## Courses

1. Open **Courses** → **+ New Course**.
2. Enter the unique course code and name. Credits, department, description and exam date/time are optional.
3. Select **Create Course** and confirm the row appears in the catalog.

Expected: the active course is available when creating a classroom section. If the code conflicts with an existing course, edit or reuse the existing record rather than inventing a duplicate. Course edits apply to the course catalog; review exam schedule values before saving.

## Classrooms and rosters

1. Open **Classrooms** → **+ New Classroom**.
2. Select the course and provide the section/class name and term, year, classroom code (the physical room label), capacity, dates, and meeting schedule as applicable. Use a stable room code such as `RM-201`; this is also how a gateway can be linked during registration.
3. Assign the teacher/faculty member, save, and confirm the new class appears in the classroom list.
4. Add students from **Students** or import a roster using the documented [CSV templates and validation rules](../guides/csv-imports.md). Review the preview before confirming an import. Resolve every invalid row rather than assuming it was accepted.
5. Activate the class when it is in session. Deactivate it when it should no longer participate in active-class matching.

Expected: the class detail shows the expected course, teacher, room code, schedule and roster count. The assigned teacher sees it in **My Classes**. If a schedule warning appears, resolve overlapping or incomplete meeting data. Activation affects matching and active classroom behavior; it is not a substitute for assigning the correct teacher.

## Devices and firmware

- Open **Modules** to inspect gateway/hub health, last-seen time and diagnostics. Use the device's exact status/reason to diagnose connectivity; do not assume that a registered device is currently online.
- Follow [device provisioning and room linking](../guides/deployment.md#3-per-room-hardware). One room normally has one gateway, one hub and its student modules.
- Upload firmware only through **Firmware**. Confirm the target, chip, version and qualification report, then use the required approval workflow. An unqualified or unsigned image may be correctly refused. Deployment preview explains excluded devices.
- Start with the canary, watch device results, and pause/cancel if failures exceed the rollout policy. Do not treat an OTA job being queued as proof that the board updated. Use the [OTA guide](../guides/ota-updates.md) and [recovery procedure](../firmware/RECOVERY_PROCEDURE.md).

## Audit, backup and restore

Use **Activity** to review administrative actions. Schedule database backups using SQLite's online backup command and include the firmware directory and secret environment file in the protected backup plan. Verify restores on a separate test installation; never experiment on the only production copy. See [backup and upgrade procedures](../guides/deployment.md#backups).
