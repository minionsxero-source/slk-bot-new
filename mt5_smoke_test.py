import os
import sys
from pathlib import Path

import MetaTrader5 as mt5

login = int(os.environ.get('MT5_LOGIN', '0'))
password = os.environ.get('MT5_PASSWORD', '')
server = os.environ.get('MT5_SERVER', 'ICMarketsSC-Demo')
terminal_path = os.environ.get('MT5_TERMINAL_PATH', '').strip()

if not login or not password:
    raise SystemExit('MT5_LOGIN and MT5_PASSWORD GitHub Secrets are required.')

print(f'MT5 terminal path: {terminal_path or "auto-discovery"}')
print(f'MT5 server: {server}')
print(f'MT5 login: {login}')

if terminal_path and not Path(terminal_path).exists():
    raise SystemExit(f'MT5 terminal executable not found: {terminal_path}')

kwargs = {'login': login, 'password': password, 'server': server, 'timeout': 60000}
ok = mt5.initialize(terminal_path, **kwargs) if terminal_path else mt5.initialize(**kwargs)
if not ok:
    print('mt5.initialize() failed:', mt5.last_error())
    raise SystemExit(1)

try:
    info = mt5.account_info()
    if info is None:
        print('account_info() failed:', mt5.last_error())
        raise SystemExit(2)

    print(f'CONNECTED: login={info.login} server={info.server} trade_mode={info.trade_mode}')
    symbols = mt5.symbols_get()
    if symbols is None:
        print('symbols_get() failed:', mt5.last_error())
        raise SystemExit(3)

    names = [s.name for s in symbols if getattr(s, 'name', None)]
    print(f'TOTAL SYMBOLS: {len(names)}')

    targets = ['EURUSD', 'XAUUSD', 'NAS100', 'DE40', 'JPN225', 'UK100', 'US30']
    for target in targets:
        matches = [n for n in names if n.upper().startswith(target)]
        if target == 'XAUUSD':
            matches += [n for n in names if n.upper().startswith('GOLD')]
        if matches:
            selected = sorted(set(matches), key=lambda x: (len(x), x))[0]
            if not mt5.symbol_select(selected, True):
                print(f'{target}: FOUND but symbol_select failed for {selected}: {mt5.last_error()}')
                continue
            rates = mt5.copy_rates_from_pos(selected, mt5.TIMEFRAME_D1, 1, 5)
            if rates is None or len(rates) == 0:
                print(f'{target}: FOUND ({selected}) but no D1 bars: {mt5.last_error()}')
            else:
                print(f'{target}: OK -> {selected}, D1 bars={len(rates)}, latest_close={float(rates[-1][4])}')
        else:
            print(f'{target}: NOT FOUND')

    print('SMOKE TEST PASSED: MT5 terminal connected and market data was queried.')
finally:
    mt5.shutdown()
