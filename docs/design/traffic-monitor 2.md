# Traffic monitor, account safety and 1PSID

## The monitor

Every API request is counted, per **origin address**, per **signed-in account** and per **kind of endpoint**, over a sliding minute. Each kind has its own limit. The limits are set high on purpose: imPress serves staff, so a flag should mean a script, a fault or an attack, not a busy lesson.

| Kind of endpoint | Per origin per minute | Per account per minute |
|---|---|---|
| sign-in (`/api/auth/login`, change password) | 60 | 60 |
| device traffic (`/api/device`, WebSocket) | 12000 | 12000 |
| live updates (`/api/events`) | 90 | 90 |
| status polling | 300 | 300 |
| reading data | 1200 | 1800 |
| changing data | 400 | 600 |
| administration (`/api/admin`) | 900 | 1200 |

- **DoS**: one origin or one account goes over the limit of one kind of endpoint.
- **DDoS**: the total for one kind is four times its limit and comes from eight or more different origins.

A flag raises an **alert for administrators and super admins** (a toast and a notification: what was seen, from where, which pages, the rate and the limit) and an entry in the activity log. Details are on *System → Security*: the origin, the pages, and the **account** when the person was signed in. The same flag is not repeated for ten minutes.

**imPress takes no action.** It never blocks, slows or signs anyone out because of traffic: that decision belongs to people. A **super admin** can sign any account out everywhere (*User access → ⋯ → Sign out everywhere*); an administrator cannot.

The monitor can be switched off with the feature `traffic_monitor` or the policy flag `traffic.monitor`. Counters are in memory and start again with the server.

## Account safety badges

Each account gets a **score from 0 to 100** from what it has done lately:

| Signal | Points |
|---|---|
| more than 1500 requests in ten minutes | up to 30 |
| more than 10 refused requests (401, 403, 422, 429) in ten minutes | up to 25 |
| used from more than two addresses at once | 15 for each extra address, up to 30 |
| a traffic flag in the last day | 20 each, up to 40 |
| refused database writes in the last day | 15 each, up to 30 |

| Score | Badge |
|---|---|
| 0 to 24 | **Safe** |
| 25 to 59 | **Potentially Unsafe** |
| 60 to 100 | **Likely Compromised** |

Hover or focus the badge to see the score and the reasons. The badge informs; it never changes what an account may do. Turn it off with the feature `risk_scores`.

## 1PSID: the first-party session identifier

A session identifier is `impress_` followed by an eight-character identity of the **server run** that issued it and 48 random bytes. The identity is created when the server starts, so **a restart ends every session**: the next request is answered `401` with `X-Session-Code: restart`, and the web app tells the person *imPress was restarted ... please sign in again*. A token copied earlier is dead after a restart. Only a SHA-256 hash of the identifier is stored; *Settings → Security* shows a 12-character fingerprint of your own, which changes with every restart.

The other reasons a session ends are reported the same way in `X-Session-Code`: `idle`, `hard` and `disabled` (the account was disabled while signed in: the page blurs and a notice explains why).
