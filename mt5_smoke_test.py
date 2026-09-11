import os
from pathlib import Path

import MetaTrader5 as mt5


# ============================================================
# ENVIRONMENT
# ============================================================

login = int(
    os.environ.get(
        "MT5_LOGIN",
        "0"
    )
)

password = os.environ.get(
    "MT5_PASSWORD",
    ""
)

server = os.environ.get(
    "MT5_SERVER",
    ""
)

terminal_path = os.environ.get(
    "MT5_TERMINAL_PATH",
    ""
).strip()


# ============================================================
# VALIDATION
# ============================================================

if not login:
    raise SystemExit(
        "ERROR: MT5_LOGIN secret is missing."
    )

if not password:
    raise SystemExit(
        "ERROR: MT5_PASSWORD secret is missing."
    )

if not server:
    raise SystemExit(
        "ERROR: MT5_SERVER secret is missing."
    )

if not terminal_path:
    raise SystemExit(
        "ERROR: MT5_TERMINAL_PATH is missing."
    )

if not Path(terminal_path).exists():
    raise SystemExit(
        f"ERROR: MT5 terminal does not exist: {terminal_path}"
    )


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SLK BOT - MT5 CONFIG CONNECTION TEST")
print("=" * 70)

print()

print("Terminal:")
print(terminal_path)

print()

print("Server:")
print(server)

print()

print("Login:")
print(login)

print()

print("Python MetaTrader5 package:")

print(
    "Author:",
    getattr(
        mt5,
        "__author__",
        "unknown"
    )
)

print(
    "Version:",
    getattr(
        mt5,
        "__version__",
        "unknown"
    )
)

print()

print("Initial MT5 API version check:")

print(
    mt5.version()
)


# ============================================================
# CONNECT
# ============================================================

print()
print("=" * 70)
print("CONNECTING TO ALREADY STARTED MT5")
print("=" * 70)

print()

print(
    "The MT5 terminal was started separately by GitHub Actions."
)

print(
    "Python will now connect to that terminal."
)

print()


ok = mt5.initialize(
    terminal_path,
    timeout=120000,
    portable=False,
)


# ============================================================
# INITIALIZE FAILED
# ============================================================

if not ok:

    print()
    print("=" * 70)
    print("INITIALIZE FAILED")
    print("=" * 70)

    print()

    error = mt5.last_error()

    print(
        "MT5 last error:"
    )

    print(
        error
    )

    print()

    if error[0] == -10005:

        print(
            "IPC TIMEOUT DETECTED."
        )

        print(
            "Python still cannot communicate with the MT5 terminal."
        )

    raise SystemExit(1)


# ============================================================
# SUCCESS
# ============================================================

try:

    print()
    print("=" * 70)
    print("INITIALIZE SUCCESSFUL")
    print("=" * 70)

    print()


    # ========================================================
    # TERMINAL INFO
    # ========================================================

    terminal_info = mt5.terminal_info()

    print("=" * 70)
    print("TERMINAL INFORMATION")
    print("=" * 70)

    print()

    if terminal_info is None:

        print(
            "terminal_info() failed:"
        )

        print(
            mt5.last_error()
        )

        raise SystemExit(2)


    print(
        "Connected:",
        terminal_info.connected
    )

    print(
        "Trade allowed:",
        terminal_info.trade_allowed
    )

    print(
        "Build:",
        terminal_info.build
    )


    # ========================================================
    # ACCOUNT
    # ========================================================

    print()
    print("=" * 70)
    print("ACCOUNT INFORMATION")
    print("=" * 70)

    print()

    account = mt5.account_info()

    if account is None:

        print(
            "account_info() failed:"
        )

        print(
            mt5.last_error()
        )

        raise SystemExit(3)


    print(
        "Login:",
        account.login
    )

    print(
        "Server:",
        account.server
    )

    print(
        "Trade mode:",
        account.trade_mode
    )

    print(
        "Currency:",
        account.currency
    )


    # ========================================================
    # SYMBOLS
    # ========================================================

    print()
    print("=" * 70)
    print("MARKET DATA TEST")
    print("=" * 70)

    print()

    symbols = mt5.symbols_get()

    if symbols is None:

        print(
            "symbols_get() failed:"
        )

        print(
            mt5.last_error()
        )

        raise SystemExit(4)


    print(
        "TOTAL SYMBOLS:",
        len(symbols)
    )


    # ========================================================
    # TARGETS
    # ========================================================

    targets = [
        "EURUSD",
        "XAUUSD",
        "NAS100",
        "DE40",
        "JPN225",
        "UK100",
        "US30",
    ]


    names = [
        symbol.name
        for symbol in symbols
        if getattr(
            symbol,
            "name",
            None
        )
    ]


    print()

    print("-" * 70)


    for target in targets:

        matches = [
            name
            for name in names
            if name.upper().startswith(
                target
            )
        ]


        # XAUUSD fallback
        if target == "XAUUSD":

            matches += [
                name
                for name in names
                if name.upper().startswith(
                    "GOLD"
                )
            ]


        if not matches:

            print(
                f"{target}: NOT FOUND"
            )

            continue


        selected = sorted(
            set(matches),
            key=lambda x: (
                len(x),
                x
            )
        )[0]


        print(
            f"{target}: {selected}"
        )


        # ----------------------------------------------------
        # Select symbol
        # ----------------------------------------------------

        if not mt5.symbol_select(
            selected,
            True
        ):

            print(
                "  symbol_select failed:"
            )

            print(
                " ",
                mt5.last_error()
            )

            continue


        # ----------------------------------------------------
        # D1 DATA
        # ----------------------------------------------------

        rates = mt5.copy_rates_from_pos(
            selected,
            mt5.TIMEFRAME_D1,
            1,
            5
        )


        if rates is None:

            print(
                "  D1 data failed:"
            )

            print(
                " ",
                mt5.last_error()
            )

            continue


        if len(rates) == 0:

            print(
                "  D1 returned zero bars."
            )

            continue


        latest_close = float(
            rates[-1][4]
        )


        print(
            f"  D1 bars: {len(rates)}"
        )

        print(
            f"  Latest closed D1 close: "
            f"{latest_close}"
        )


    # ========================================================
    # FINAL SUCCESS
    # ========================================================

    print()
    print("=" * 70)
    print("SMOKE TEST PASSED")
    print("=" * 70)

    print()

    print(
        "MT5 terminal connected."
    )

    print(
        "Account information was retrieved."
    )

    print(
        "Market data was queried."
    )

    print()


finally:

    mt5.shutdown()

    print(
        "MT5 connection closed."
    )
