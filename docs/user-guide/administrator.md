# Administrator guide

Use a personal administrator account for routine work. The application checks permissions on the server; hiding a button in the browser is not a permission boundary. A `super_admin` can manage administrator accounts and installation-wide settings; an `admin` manages day-to-day teaching data and devices within the permissions the server grants.

## Accounts and the account lifecycle

Open **User access** (the *Accounts* tab). Full detail, including the password rule and the welcome set-up, is in [accounts, first sign-in and the default super admin](../guides/accounts-and-onboarding.md).

1. Choose **Add account**. Enter the full name, an optional display name, a unique username and the e-mail address. Choose **Faculty** for an instructor (and *Teaching assistant* if you want the account shown that way: the permissions are the same). Give **Administrator** only to staff who need to administer classrooms, students or devices (only a super admin can).
2. Choose the first password: **generate one** (shown once, with a copy button) or type one. The strength meter and the rule (8+ characters with upper and lower case, a number and a special character) apply as you type.
3. Give the person the temporary password in person or through a private channel. They sign in, **choose their own password**, say what to call them, pick a look and are offered a short tour.
4. Use the row's buttons: **Disable** (signs the person out at once; if they are using imPress they see a clear notice) or **Enable**; the **⋯** menu has *Edit details*, *Activity history*, *Make faculty / administrator*, *Make teaching assistant / faculty*, *Reset password*, *Sign out everywhere* (super admins) and *Delete account*.
5. **Delete** moves an account to **Deleted**, where it can be restored for **30 days** before it is removed permanently.

Other tabs: **Active now** (who is signed in, from where, and their last activity, with a history chart per person) and **Deleted**. Each account has a **safety badge**: *Safe*, *Potentially Unsafe* or *Likely Compromised* (hover for the score and reasons); see the [traffic monitor](../design/traffic-monitor.md). Switching a person between faculty and administrator asks you to confirm; between faculty and TA it shows a warning that only the label changes.

Expected: the account appears with its role and status (*Pending setup* until the person has chosen a password). Duplicate usernames and e-mails, weak passwords and attempts to remove the last active super administrator are refused with an explanation. Super admin accounts cannot be created here: root creates them in the [console](../guides/console.md).

If every super administrator is somehow unavailable, imPress's own [deadlock prevention](../guides/accounts-and-onboarding.md#global-deadlock-prevention) restores the database and creates a recovery account; the server-side [recovery procedure](../guides/deployment.md#recovering-administrator-access) is the manual way.

## Features, backups and the system

*System → Features* switches parts of imPress on or off for everyone (the order of authority and the change log are explained in [launch flags and features](../guides/launch-flags.md#features)); *Requirements* shows what the host was found to have; *Backups* saves and restores the database and system state ([guide](../guides/backups.md)); *Security* shows unusual-traffic alerts. Your own look and layout are in [Settings](../guides/personalization.md); *Advanced mode* there shows more detail on the dashboard.

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
