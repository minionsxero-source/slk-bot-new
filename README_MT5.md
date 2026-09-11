# SLK Bot — IC Markets MT5 Demo

This build uses the IC Markets MT5 terminal as the market-data source. It is **read-only**: it requests W1, D1 and H4 bars and does not place orders.

## 1. Install IC Markets MT5
Install and open the IC Markets MetaTrader 5 terminal. Log into the demo account using your IC Markets credentials and server `ICMarketsSC-Demo`.

## 2. Install Python dependencies
Open Command Prompt in this folder:

```bat
py -3.14 -m pip install -r requirements.txt
```

## 3. Create `.env`
Copy `.env.example` to `.env` and enter your MT5 login and password locally. **Never send the password in chat.**

Example:

```text
DATA_PROVIDER=MT5
MT5_LOGIN=YOUR_LOGIN
MT5_PASSWORD=YOUR_PASSWORD
MT5_SERVER=ICMarketsSC-Demo
```

## 4. Run the scanner

```bat
py -3.14 main.py
```

The MT5 adapter requests bars starting at position 1, so the current forming bar (position 0) is excluded. This keeps the SLK engine on closed candles.

## 5. First-run alert protection

By default, the first scan uses `SLK_BOOTSTRAP_SILENT=true`. It records already-existing storylines in `.slk_state.json` without printing them as new alerts. This prevents historical signals from being treated as fresh alerts.

On later scans, only a changed storyline event key is emitted. Re-running the scanner against the same candles does not duplicate the alert.

If you deliberately want the first run to print existing historical signals, set:

```text
SLK_BOOTSTRAP_SILENT=false
```

## 6. Production
For production, the MT5 terminal and scanner can later be moved to a Windows VPS so your personal PC does not need to remain on.


## v2.6 Full Audit Mode
Set `SYMBOLS=ALL_SYMBOLS`. The scanner discovers every symbol exposed by the connected MT5 terminal and audits W1/D1/H4. Telegram and bootstrap suppression are disabled in this build so historical decisions are visible for engine validation.
