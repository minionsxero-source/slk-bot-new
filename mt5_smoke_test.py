import os
from pathlib import Path

import MetaTrader5 as mt5


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

login = int(
    os.environ.get("MT5_LOGIN", "0")
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
# BASIC VALIDATION
# ============================================================

if not login:
    raise SystemExit(
        "ERROR: MT5_LOGIN GitHub Secret is missing."
    )

if not password:
    raise SystemExit(
        "ERROR: MT5_PASSWORD GitHub Secret is missing."
    )

if not server:
    raise SystemExit(
        "ERROR: MT5_SERVER GitHub Secret is missing."
    )

if not terminal_path:
    raise SystemExit(
        "ERROR: MT5_TERMINAL_PATH was not provided."
    )


if not Path(terminal_path).exists():
    raise SystemExit(
        f"ERROR: MT5 terminal not found: {terminal_path}"
    )


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SLK BOT - MT5 CONNECTION DIAGNOSTIC")
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

print("MetaTrader5 Python package:")
print("Author:", getattr(
    mt5,
    "__author__",
    "unknown"
))

print(
    "Version:",
    getattr(
        mt5,
        "__version__",
        "unknown"
    )
)

print()

print("MT5 Python API version:")
print(mt5.version())

print()


# ============================================================
# INITIALIZE MT5
# ============================================================

print("=" * 70)
print("ATTEMPTING MT5 INITIALIZE")
print("=" * 70)

print()

ok = mt5.initialize(
    terminal_path,
    login=login,
    password=password,
    server=server,
    timeout=120000,
    portable=False,
)


# ============================================================
# INITIALIZATION FAILURE
# ============================================================

if not ok:

    print()
    print("=" * 70)
    print("INITIALIZE FAILED")
    print("=" * 70)

    print()

    print(
        "MT5 last error:"
    )

    print(
        mt5.last_error()
    )

    print()

    print(
        "This means Python could not establish "
        "IPC communication with the MT5 terminal."
    )

    print()

    raise SystemExit(1)


# ============================================================
# CONNECTION SUCCESS
# ============================================================

try:

    print()
    print("=" * 70)
    print("INITIALIZE SUCCESSFUL")
    print("=" * 70)

    print()

    print(
        "Python successfully connected to MT5."
    )


    # ========================================================
    # TERMINAL INFORMATION
    # ========================================================

    print()
    print("=" * 70)
    print("TERMINAL INFORMATION")
    print("=" * 70)

    terminal_info = mt5.terminal_info()

    if terminal_info is None:

        print(
            "terminal_info() failed:"
        )

        print(
            mt5.last_error()
        )

        raise SystemExit(2)

    print()

    print(
        "Connected:",
        terminal_info.connected
    )

    print(
        "Trade allowed:",
        terminal_info.trade_allowed
    )

    print(
        "Community account:",
        terminal_info.community_account
    )

    print(
        "Build:",
        terminal_info.build
    )


    # ========================================================
    # ACCOUNT INFORMATION
    # ========================================================

    print()
    print("=" * 70)
    print("ACCOUNT INFORMATION")
    print("=" * 70)

    account = mt5.account_info()

    if account is None:

        print(
            "account_info() failed:"
        )

        print(
            mt5.last_error()
        )

        raise SystemExit(3)

    print()

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
    # SYMBOL TEST
    # ========================================================

    print()
    print("=" * 70)
    print("SYMBOL / MARKET DATA TEST")
    print("=" * 70)

    symbols = mt5.symbols_get()

    if symbols is None:

        print(
            "symbols_get() failed:"
        )

        print(
            mt5.last_error()
        )

        raise SystemExit(4)

    print()

    print(
        "TOTAL SYMBOLS:",
        len(symbols)
    )


    # ========================================================
    # TARGET SYMBOLS
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

        # ----------------------------------------------------
        # Find matching broker symbol
        # ----------------------------------------------------

        matches = [
            name
            for name in names
            if name.upper().startswith(
                target
            )
        ]


        # ----------------------------------------------------
        # GOLD / XAUUSD fallback
        # ----------------------------------------------------

        if target == "XAUUSD":

            matches += [
                name
                for name in names
                if name.upper().startswith(
                    "GOLD"
                )
            ]


        # ----------------------------------------------------
        # Symbol not found
        # ----------------------------------------------------

        if not matches:

            print(
                f"{target}: NOT FOUND"
            )

            continue


        # ----------------------------------------------------
        # Choose shortest matching symbol
        # ----------------------------------------------------

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

        selected_ok = mt5.symbol_select(
            selected,
            True
        )

        if not selected_ok:

            print(
                "  symbol_select failed:"
            )

            print(
                " ",
                mt5.last_error()
            )

            continue


        # ----------------------------------------------------
        # Request D1 data
        # ----------------------------------------------------

        rates = mt5.copy_rates_from_pos(
            selected,
            mt5.TIMEFRAME_D1,
            1,
            5,
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
                "  D1 data returned zero bars."
            )

            continue


        # ----------------------------------------------------
        # Latest closed D1 candle
        # ----------------------------------------------------

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
    # SUCCESS
    # ========================================================

    print()
    print("=" * 70)
    print("SMOKE TEST PASSED")
    print("=" * 70)

    print()

    print(
        "MT5 terminal connected successfully."
    )

    print(
        "Market data was successfully queried."
    )

    print()


# ============================================================
# CLEAN SHUTDOWN
# ============================================================

finally:

    mt5.shutdown()

    print(
        "MT5 connection closed."
    )
