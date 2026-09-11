# SLK Bot v2.8.3 — IC Markets MT5

This version adds a daily-close production scan while keeping the SLK engine read-only.

## Daily-close rule
At **02:35 IST** by default (five minutes after the user's stated 02:30 daily market close), the bot scans **every symbol exposed by IC Markets MT5**. After that, it repeats the full scan every 4 hours: **02:35, 06:35, 10:35, 14:35, 18:35, 22:35 IST**.

For each symbol it checks:
1. Daily fresh Open/Close key-level rejection **OR** confirmed previous-day liquidity sweep.
2. Required H4 lower-timeframe breakout.
3. External breakout must be completed with a closed-candle body break.
4. Only completed external-breakout storylines are sent to Telegram.
5. Internal-only or rejection-without-breakout cases are not sent as alerts.
6. Event de-duplication prevents the same completed storyline from being sent repeatedly.

When the scheduled bot starts, it performs **one immediate full scan** first. It then waits for the next fixed 4-hour slot anchored at 02:35 IST and continues every 4 hours. The scheduled scan is deliberately **Daily-only** for the trigger path. Weekly rejection scanning remains available in audit mode.

## Immediate startup scan + scheduled scanning
```bat
py -3.14 main.py
```
Set `RUN_MODE=AUDIT`.

## Run scheduled Telegram scanner
Set:
```text
RUN_MODE=SCHEDULED
DAILY_SCAN_HOUR=2
DAILY_SCAN_MINUTE=35
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```
Then:
```bat
py -3.14 main.py
```
Keep the IC Markets MT5 terminal and this Python process running. For a true 24/7 setup, move both to a Windows VPS.

## Important
The bot never places trades. Alerts are bias/storyline only; there is no entry, SL or TP.


## v2.8.8 target universe
The scanner is restricted to all broker-exposed variants of the 28 traditional major/minor FX pairs, only these five index families: JPN225, GER40, NAS100, UK100, and US30, plus gold (XAUUSD/GOLD). All other indices, individual stocks, crypto, energies, silver/other metals, and unrelated CFDs are excluded.


## v2.8.8 strict daily event behavior
- Daily-close scans only accept a rejection on the latest completed D1 candle.
- Older D1 rejection events are never revived or re-alerted.
- A current D1 liquidity sweep remains eligible under the user-specific sweep rule.
- H4 External BO is still required before Telegram alerting.
- Startup scan remains enabled for testing; it uses the same strict latest-D1 event filter.
- Target universe remains major/minor FX + broker-exposed indices + gold only.


## Liquidity-sweep-only signal rule
A confirmed Daily liquidity sweep can substitute for a Daily OC-shape rejection.
If the latest completed Daily candle sweeps the previous day's HIGH and closes back
below it, the direction is BEARISH; the H4 External BO must also be BEARISH.
If it sweeps the previous day's LOW and closes back above it, the direction is
BULLISH; the H4 External BO must also be BULLISH. Sweep + matching H4 External BO
produces a Telegram storyline alert even when there is no Daily OC rejection.
An opposite-direction H4 BO produces no signal.


## v2.8.9 scan behavior

- Startup: immediate H4 running scan.
- Every 4 hours: running H4 scan.
- At 02:35 IST: strict Daily-close scan of the newly completed D1 candle, then H4 confirmation.
- Running H4 scan checks either an active Daily OC rejection + matching H4 external BO, or an H4 sweep of the previous day's high/low + matching H4 external BO.
- A high sweep is bearish; a low sweep is bullish. Opposite-direction BO does not qualify.
- Telegram prices are displayed to exactly 4 decimal places.

## User access control
Users can message `/start` then `/request_access`, submit their email, and receive a pending-approval message. The admin receives the request and can approve with `/approve CHAT_ID EURUSD,XAUUSD,NAS100` or use the web admin panel at `http://SERVER-IP:8080/`.

Approved users receive alerts only for pairs assigned to them. Use `/requests`, `/users`, `/pairs CHAT_ID PAIR1,PAIR2`, `/disable CHAT_ID`, and `/reject CHAT_ID` from the admin Telegram account.

Set `ADMIN_TELEGRAM_ID`, `ADMIN_PANEL_PORT`, and a strong `ADMIN_PANEL_PASSWORD` in `.env`.

## Vercel Admin + Access Website
The `vercel-admin/` folder is a Vercel-ready Next.js admin/access application. It shares access state through Supabase with the Python Telegram bot when the bot is configured with `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

Deploy `vercel-admin/` as a separate Vercel project. Run `vercel-admin/supabase.sql` in Supabase first. See `vercel-admin/README.md`.
