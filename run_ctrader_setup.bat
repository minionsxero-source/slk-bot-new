@echo off
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install ctrader-oauth-fetcher

echo.
echo Dependencies installed.
echo Next: create/approve your cTrader Open API application and generate OAuth tokens.
pause
