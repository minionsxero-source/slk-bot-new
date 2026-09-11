# IC Markets cTrader connection

This build uses cTrader Open API as a **read-only market-data source** for the SLK scanner. The bot does not place trades.

## Required

1. An IC Markets **cTrader** account.
2. A cTrader Open API application with Client ID and Client Secret.
3. OAuth access + refresh tokens authorized for the account.
4. Your IC Markets cTrader trader login number.

## Environment

Copy `.env.example` to `.env` and fill:

- `CTRADER_CLIENT_ID`
- `CTRADER_CLIENT_SECRET`
- `CTRADER_TRADER_LOGIN`
- `CTRADER_ACCESS_TOKEN`
- `CTRADER_REFRESH_TOKEN`
- `CTRADER_EXPIRES_AT`

Keep `.env` private. Never commit it to GitHub.

## OAuth helper

With Python 3.14 you can use:

`uvx ctrader-oauth-fetcher --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --scope accounts --redirect-uri http://localhost:8080`

The scanner only needs account/market-data access, so the recommended first connection is the read-only `accounts` scope. If the token is rejected for the required market-data account access, use the scope required by your cTrader setup; do not enable trading just for the scanner.

The official cTrader Open API uses OAuth 2.0. Access tokens expire and refresh tokens are used to renew them. The bot persists rotated tokens in `.ctrader_tokens.json` so a refresh does not silently invalidate the next run.

## First run

Set:

`DATA_PROVIDER=CTRADER`

Then:

`python run_once.py`

The bot will:

1. authenticate the cTrader application;
2. authenticate your IC Markets cTrader account;
3. discover the account's symbols;
4. download closed W1/D1/H4 candles;
5. run the SLK engine;
6. print only new SLK events.

No order is submitted.
