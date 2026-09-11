import os
from pathlib import Path

import MetaTrader5 as mt5


login = int(os.environ.get("MT5_LOGIN", "0"))
password = os.environ.get("MT5_PASSWORD", "")
server = os.environ.get("MT5_SERVER", "")
terminal_path = os.environ.get("MT5_TERMINAL_PATH", "").strip()


if not login or not password:
    raise SystemExit("MT5_LOGIN and MT5_PASSWORD GitHub Secrets are required.")

if not server:
    raise SystemExit("MT5_SERVER GitHub Secret is required.")

if not terminal_path:
    raise SystemExit("MT5_TERMINAL_PATH was not provided.")

if not Path(terminal_path).exists():
    raise SystemExit(f"MT5 terminal not found: {terminal_path}")


print("=" * 60)
print("MT5 CONNECTION DIAGNOSTIC")
print("=" * 60)

print(f"Terminal: {terminal_path}")
print(f"Server: {server}")
print(f"Login: {login}")

print()
print("Python MetaTrader5 package:")
print("Author:", getattr(mt5, "__author__", "unknown"))
print("Version:", getattr(mt5, "__version__", "unknown"))

print()
print("MT5 version:")
print(mt5.version())


print()
print("Attempting initialize...")

ok = mt5.initialize(
    terminal_path,
    login=login,
    password=password,
    server=server,
    timeout=120000,
    portable=False,
)


if not ok:
    print()
    print("INITIALIZE FAILED")
    print("Error:", mt5.last_error())
    raise SystemExit(1)


try:
    print()
    print("INITIALIZE SUCCESSFUL")

    terminal_info = mt5.terminal_info()

    print()
    print("TERMINAL INFO:")
    print(terminal_info)

    if terminal_info is None:
        print("terminal_info() failed:", mt5.last_error())
        raise SystemExit(2)

    account = mt5.account_info()

    print()
    print("ACCOUNT INFO:")

    if account is None:
        print("account_info() failed:", mt5.last_error())
        raise SystemExit(3)

    print(
        f"login={account.login} "
        f"server={account.server} "
        f"trade_mode={account.trade_mode}"
    )

    symbols = mt5.symbols_get()

    if symbols is None:
        print("symbols_get() failed:", mt5.last_error())
        raise SystemExit(4)

    print()
    print(f"TOTAL SYMBOLS: {len(symbols)}")

    targets = [
        "EURUSD",
        "XAUUSD",
        "NAS100",
        "DE40",
        "JPN225",
        "UK100",
        "US30",
    ]

    print()
    print("TESTING TARGET SYMBOLS")
    print("-" * 60)

    names = [
        s.name
        for s in symbols
        if getattr(s, "name", None)
    ]

    for target in targets:

        matches = [
            name
            for name in names
            if name.upper().startswith(target)
        ]

        if target == "XAUUSD":
            matches += [
                name
                for name in names
                if name.upper().startswith("GOLD")
            ]

        if not matches:
            print(f"{target}: NOT FOUND")
            continue

        selected = sorted(
            set(matches),
            key=lambda x: (len(x), x)
        )[0]

        print(f"{target}: {selected}")

        if not mt5.symbol_select(selected, True):
            print(
                f"  symbol_select failed: "
                f"{mt5.last_error()}"
            )
            continue

        rates = mt5.copy_rates_from_pos(
            selected,
            mt5.TIMEFRAME_D1,
            1,
            5,
        )

        if rates is None or len(rates) == 0:
            print(
                f"  D1 data failed: "
                f"{mt5.last_error()}"
            )
            continue

        print(
            f"  D1 bars: {len(rates)}"
        )

        print(
            f"  Latest closed D1 close: "
            f"{float(rates[-1][4])}"
        )

    print()
    print("=" * 60)
    print("SMOKE TEST PASSED")
    print("MT5 terminal connected and market data was queried.")
    print("=" * 60)

finally:
    mt5.shutdown()
