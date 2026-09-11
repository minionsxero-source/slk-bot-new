# GitHub Actions MT5 test

This workflow is intentionally a **manual smoke test**. It does not run the SLK scanner, does not send Telegram alerts, and does not modify Supabase.

## Required GitHub Secrets

Repository → Settings → Secrets and variables → Actions → New repository secret:

- `MT5_LOGIN` — demo MT5 account number
- `MT5_PASSWORD` — demo MT5 password
- `MT5_SERVER` — exact IC Markets MT5 server name, for example `ICMarketsSC-Demo`

The workflow installs the standard MetaTrader 5 Windows terminal, connects using the MetaTrader 5 Python integration, and queries D1 data for several target instruments.

## Run it

GitHub → Actions → **MT5 Windows Smoke Test** → **Run workflow**.

A successful run should end with:

`SMOKE TEST PASSED: MT5 terminal connected and market data was queried.`

GitHub-hosted Windows runners are ephemeral: a fresh Windows VM is created for each job and discarded after the job. This workflow is therefore a test of whether MT5 can run inside GitHub Actions, not a 24/7 server.
