# Personalization, accessibility, search and the dashboard

Everything on this page follows **your account**: set it once and it is the same on every computer you sign in from. Each setting applies the moment you change it. Open *Settings* (the avatar menu or the sidebar), or change the common ones from the search palette without leaving the page you are on.

## Search and quick settings

Press **Ctrl K** (**⌘ K** on a Mac) or **/**, or click *Search or jump to…* in the top bar.

- Type two or more characters to search **classrooms, students, courses, quizzes, polls**, and, for administrators, **accounts and devices**. Results are limited to what you may see: faculty find only their own classrooms and the students they registered or teach.
- Pages and **settings** match too. A setting appears as a **live widget**: change the theme, accent colour, reduced motion, contrast, text size, colour vision mode, sidebar, time and date format (and advanced mode for administrators) right there, without opening Settings.
- Arrow keys move, Enter opens, Esc closes.

## Appearance

| Setting | Choices |
|---|---|
| Theme | Light, Dark, or Auto (follow the device). Changing it plays a circular reveal from the button you pressed, or a short cross-fade, or nothing with *Reduce motion* |
| Accent colour | Indigo, blue, teal, green, amber, rose, violet, slate, or any colour you choose |
| Density | Comfortable or Compact |
| Sidebar | Collapse it to icons with the arrow at its top, or press **[**. Hover an icon for its name. The choice is remembered |

## Accessibility

imPress works with a keyboard and a screen reader: pages have landmarks, headings and a *Skip to content* link; controls have names; dialogs trap and return focus; status changes are announced; every status carries a shape as well as a colour (✓ ▲ ✕).

| Setting | What it does |
|---|---|
| Reduce motion | no animations or transitions at all (it also follows the device's setting by default) |
| Increase contrast | stronger text and borders, thicker focus outlines, underlined links |
| Text size | *Smaller*, *Default*, *Larger*, *Largest* (no numbers) |
| Colour vision | *Protanopia*, *Deuteranopia*, *Tritanopia* or *Monochrome*: good, warning, bad and information move to colours a person with that deficiency can tell apart |

## Date, time and numbers

Times are shown in Indian Standard Time (the server's clock). You choose how they are written, and the preview below the settings shows the result.

| Setting | Choices |
|---|---|
| Date format | `31/12/2026`, `12/31/2026`, `2026/12/31`, `31 Dec 2026`, `2026-12-31` |
| Time format | 24-hour or 12-hour; seconds on or off |
| Week starts on | Monday, Sunday, Saturday (the order of days in a timetable) |
| Numbers | `1,234.5`, `1.234,5`, `1 234,5` |
| Relative times | "5 min ago", or the exact time |
| Start page | where you land after signing in: Overview, Classrooms, Students (administrators) |

## The dashboard

The Overview is a grid of **widgets**. Press **Customise**:

- **drag** a widget to move it; **resize** with the corner button (small, medium, large, full width); **remove** with the ✕;
- **Add widget** opens the gallery, grouped by what the widget shows. Several widgets show the same information in different ways, for example *students* as a number, as bars per classroom, or as a ring; *classrooms* as a number, a status ring or today's list;
- **Reset to default** brings back the standard layout. Your layout is saved with your account.

Faculty can add widgets about their classrooms, students, quizzes and polls. Administrators also get devices, accounts, who is active now, recent activity, system health and a table of today's classrooms.

### Advanced mode (administrators)

*Settings → Advanced mode* is **off by default**. Off, the dashboard is simple: the main figures. On, the widgets show more detail (averages, breakdowns, answers received, backups, the address people are signed in from) and two more widgets become available: **Account safety** and **Unusual traffic**. It is saved for your account only and has no effect on what you are allowed to do.

## Notifications

The bell shows a count of unread alerts. Open it for the tray: notifications are grouped by day, newest first, with *All* and *Alerts* tabs, *Mark all read* and *Clear all*; dismiss one with its ✕. Alerts about the system (for administrators) and your classrooms arrive as they happen.

## The guided tour and help

The **?** button in the top bar opens *Take the tour*, *Keyboard shortcuts* and (administrators only) *Help & documentation*. Faculty do not see the documentation menu.

| Key | Does |
|---|---|
| Ctrl/⌘ K or / | search |
| [ | collapse or expand the sidebar |
| ? | the shortcut list |
| Esc | close a dialog, the search or the tour |

## Notices that cover the page

- **Your account was disabled** while you were using imPress: the page blurs and a notice explains it, with a button back to sign-in.
- **A system update is running** (a firmware rollout, for administrators' and faculty alike): the page blurs and says *Updating imPress* ... until it has finished, then returns by itself.
- **imPress restarted:** every session ends when the server restarts; the notice asks you to sign in again.

All three can be switched off by an administrator (features `disabled_overlay`, `update_overlay`); a restart notice is always shown.
