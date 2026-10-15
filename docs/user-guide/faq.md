# Frequently asked questions

## I can open the page locally but another computer cannot sign in

The local address `127.0.0.1` works only on the server computer. For a remote browser, use the configured HTTPS URL and firewall rule. imPress refuses staff login over remote plain HTTP by default. See [container networking](../deployment/container.md#network-requirements) and [TLS setup](../guides/deployment.md#tls-reverse-proxy-websockets-included).

## The first admin password is not in the browser

It is printed once in the server log on the first start if `IMPRESS_INITIAL_ADMIN_PASSWORD` was empty. Retrieve it from that protected server log. Do not ask for or publish demo-account plaintext passwords. After login, change the password in **Settings**.

## A teacher cannot see a class

Ask an administrator to verify that the teacher account is active and assigned to that exact class. The administrator should also verify the class is not archived/inactive. Avoid granting a broader role to work around a missing assignment.

## A device is registered but offline

Registration does not prove current connectivity. Check **Modules** for last-seen time and diagnostic reason. Verify the 2.4 GHz Wi-Fi credentials, backend hostname/port, matching device key, firewall, room link and S3 mesh channel. Follow [gateway and hub first boot](../guides/troubleshooting.md#gateway-and-hub-first-boot).

## Can student modules receive OTA updates?

Not currently. Student-module OTA over ESP-NOW is a separate feature and requires hardware validation. Flash student modules over serial using the [firmware flashing procedure](../guides/deployment.md#3-per-room-hardware).

## Why was a firmware upload or deployment refused?

Open the firmware image's qualification report and deployment preview. Common reasons include a wrong target/chip, malformed or oversized image, missing signature, stale image file, unavailable qualification worker, or a device that cannot safely accept that target. Do not bypass the refusal; see [OTA safety and signing](../guides/ota-updates.md).

## A migration failed or an upgrade changed the database

Do not delete the database or repeatedly restart blindly. Preserve the server log and the migration backup, then follow [database migration recovery](../engineering/DATABASE_MIGRATIONS.md) or contact a maintainer with sanitized diagnostics.

## Where should I report a problem?

Check [known issues](../reference/known-issues.md) and search the project issue tracker first. A useful report includes version/commit, role, device model, safe reproduction steps, expected and observed results, and sanitized logs. Never include passwords, API keys, student information, firmware signing keys, or private session tokens.
