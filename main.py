import asyncio, json, os, threading
from datetime import datetime, timedelta
from pathlib import Path
from datetime import timezone
from slk_bot.config import Settings
from slk_bot.data_mt5 import build_client_from_env
from slk_bot.ohlc import validate_series
from slk_bot.strategy import evaluate_storyline, evaluate_daily_close_scan, evaluate_h4_running_scan
from slk_bot.telegram import TelegramNotifier
from slk_bot.access_bot import AccessBot
from slk_bot.admin_panel import Panel

STATE_FILE = Path(".slk_state.json")
STATE_VERSION = 3
IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def load_state():
    if not STATE_FILE.exists():
        return {"version": STATE_VERSION, "events": {}, "daily_runs": {}}
    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": STATE_VERSION, "events": {}, "daily_runs": {}}
    if not isinstance(raw, dict):
        return {"version": STATE_VERSION, "events": {}, "daily_runs": {}}
    # Migrate the older format: {"EURUSD": "event-key", ...}
    if "events" not in raw:
        return {"version": STATE_VERSION, "events": raw, "daily_runs": {}}
    events = raw.get("events") if isinstance(raw.get("events"), dict) else {}
    daily_runs = raw.get("daily_runs") if isinstance(raw.get("daily_runs"), dict) else {}
    return {"version": STATE_VERSION, "events": events, "daily_runs": daily_runs}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _event_key(symbol: str, result) -> str:
    rejection_time = result.rejection.candle_time.isoformat() if result.rejection else ""
    internal_time = result.internal_bo.candle_time.isoformat() if result.internal_bo else ""
    external_time = result.external_bo.candle_time.isoformat() if result.external_bo else ""
    internal_level = f"{result.internal_bo.level_price:.10f}" if result.internal_bo else ""
    external_level = f"{result.external_bo.level_price:.10f}" if result.external_bo else ""
    return "|".join((str(STATE_VERSION), symbol, result.rejection_timeframe, result.direction,
        result.status, rejection_time, internal_time, internal_level, external_time, external_level))


def _fmt_price(value: float) -> str:
    # Four decimals, truncated rather than rounded.
    import math
    return f"{math.trunc(value * 10000) / 10000:.4f}"


def _fmt_time(dt) -> str:
    return (dt.strftime("%a %d %b, %H:%M UTC").replace(" 0", " ", 1)) if dt else ""


def format_result(r):
    if r.status == "NO SIGNAL":
        return ""
    tf = r.rejection.timeframe if r.rejection else r.rejection_timeframe
    setup_tf = "W1" if tf == "W1" else "D1"
    breakout_tf = "D1" if tf == "W1" else "H4"
    arrow = f"{setup_tf}→{breakout_tf}"
    emoji = "🟢" if r.direction == "BULLISH" else "🔴"
    # Completed alerts use the compact user-requested storyline format.
    # Internal BO is shown as a supporting state; the external BO is the
    # completion event. Do not add a redundant status/confirmation field.
    if r.external_bo and r.reason == "LIQUIDITY SWEEP" and r.rejection_timeframe == "H4":
        headline = "H4 liquidity sweep + external breakout confirmed"
    elif r.external_bo and r.reason in {"FRESH KEY LEVEL REJECTION", "KL REJECTION + LIQUIDITY SWEEP"}:
        headline = "Daily key-level rejection + external breakout confirmed"
    else:
        headline = "External breakout confirmed" if r.external_bo else (
            "Internal BO: DONE — waiting for external breakout" if r.internal_bo
            else "Waiting for external breakout"
        )
    lines = [f"{emoji} {r.direction} · {r.symbol} · {arrow}", headline, ""]
    # A liquidity-sweep-only storyline uses a synthetic rejection internally
    # for the H4 structure search, but must NOT be presented as an OC-shape
    # rejection to the user. The actual trigger is the sweep.
    if r.sweep and r.rejection and r.reason == "LIQUIDITY SWEEP":
        lines.append(f"Liquidity sweep: {r.sweep.side} @ {_fmt_price(r.sweep.price)}")
        lines.append(f"Swept {_fmt_time(r.sweep.candle_time)}")
    elif r.rejection:
        rejection_bias = "BULLISH" if r.rejection.key_level.kind == "SUPPORT" else "BEARISH"
        lines.append(f"{rejection_bias} rejection at OC-shape @ {_fmt_price(r.rejection.key_level.price)}, {r.rejection.key_level.kind}.")
        lines.append(f"Rejected {_fmt_time(r.rejection.candle_time)}")
        if r.sweep:
            lines.append(f"Liquidity sweep: {r.sweep.side} @ {_fmt_price(r.sweep.price)}")
    lines.append(f"Internal BO: DONE — Broke {_fmt_price(r.internal_bo.level_price)}" if r.internal_bo else "Internal BO: NOT DETECTED")
    lines.append(f"External BO: DONE — Broke {_fmt_price(r.external_bo.level_price)}" if r.external_bo else "External BO: NOT DETECTED")
    lines.append(f"Weekly trend: {r.weekly_direction}")
    lines.append(f"Daily trend: {r.daily_direction}")
    lines.append("⚠️ Not an entry signal. Bias only — wait for your entry model.")
    return "\n".join(lines)


async def discover_and_load(client, settings):
    # Scheduled production scans always use every symbol exposed by IC Markets MT5.
    # This prevents an old .env SYMBOLS list from silently restricting the scan.
    symbols = await client.discover_symbols()
    return symbols


async def scan_symbol(client, settings, symbol, evaluator):
    data = {}
    for tf in settings.timeframes:
        candles = await client.candles(symbol, tf, settings.history_size)
        validate_series(candles)
        data[tf] = candles
    return evaluator(symbol, data["W1"], data["D1"], data["H4"])


async def audit_once(settings: Settings):
    print("=" * 72, flush=True)
    print("SLK ENGINE v2.8.8 — STRICT DAILY EVENT | FX + INDICES + GOLD", flush=True)
    print("=" * 72, flush=True)
    print(f"Requested symbols: {', '.join(settings.symbols)}", flush=True)
    print(f"Daily scan: {settings.daily_scan_hour:02d}:{settings.daily_scan_minute:02d} Asia/Kolkata", flush=True)
    print("Telegram: DISABLED IN AUDIT MODE", flush=True)
    print("", flush=True)
    async with build_client_from_env(settings) as client:
        import MetaTrader5 as mt5
        account = mt5.account_info()
        print(f"MT5 connection: OK | Login: {int(account.login)} | Server: {account.server}", flush=True)
        symbols = await discover_and_load(client, settings)
        print(f"Target symbols returned: {len(symbols)}", flush=True)
        counts = {"SIGNAL":0,"WAIT":0,"NO SIGNAL":0,"DATA ERROR":0}
        for idx, symbol in enumerate(symbols, 1):
            print(f"[{idx}/{len(symbols)}] {symbol}", flush=True)
            try:
                result = await scan_symbol(client, settings, symbol, evaluate_storyline)
            except Exception as exc:
                counts["DATA ERROR"] += 1
                print(f"  DATA ERROR: {type(exc).__name__}: {exc}", flush=True)
                continue
            if result.status == "NO SIGNAL":
                counts["NO SIGNAL"] += 1
                print(f"  DECISION: NO SIGNAL | {result.reason}", flush=True)
            elif result.external_bo:
                counts["SIGNAL"] += 1
                print("  DECISION: STORYLINE CONFIRMED", flush=True)
            else:
                counts["WAIT"] += 1
                print(f"  DECISION: WAIT | {result.status}", flush=True)
            print(f"  Direction: {result.direction} | Weekly: {result.weekly_direction} | Daily: {result.daily_direction}", flush=True)
            print(f"  Reason: {result.reason}", flush=True)
        print("=" * 72, flush=True)
        print(f"AUDIT COMPLETE | Symbols: {len(symbols)} | Confirmed: {counts['SIGNAL']} | Wait: {counts['WAIT']} | No signal: {counts['NO SIGNAL']} | Errors: {counts['DATA ERROR']}", flush=True)
        print("=" * 72, flush=True)


async def _run_production_scan(settings: Settings, notifier: TelegramNotifier, access_bot: AccessBot, state: dict, label: str, evaluator=evaluate_h4_running_scan):
    print("=" * 72, flush=True)
    print(f"Starting SLK scan: {label} IST", flush=True)
    print("=" * 72, flush=True)
    async with build_client_from_env(settings) as client:
        symbols = await discover_and_load(client, settings)
        print(f"Scanning {len(symbols)} symbols for Daily rejection OR H4 previous-day sweep + matching H4 external breakout", flush=True)
        sent = 0
        errors = 0
        for idx, symbol in enumerate(symbols, 1):
            try:
                result = await scan_symbol(client, settings, symbol, evaluator)
            except Exception as exc:
                errors += 1
                print(f"[{idx}/{len(symbols)}] {symbol} DATA ERROR: {exc}", flush=True)
                continue
            if not result.external_bo:
                continue
            key = _event_key(symbol, result)
            if state["events"].get(symbol) == key:
                print(f"[{idx}/{len(symbols)}] {symbol} duplicate storyline — skipped", flush=True)
                continue
            text = format_result(result)
            if not text:
                continue
            await notifier.send(text)
            delivered = await access_bot.broadcast_alert(symbol, text)
            state["events"][symbol] = key
            sent += 1
            print(f"[{idx}/{len(symbols)}] ALERT SENT: {symbol} | recipients: {delivered}", flush=True)
        state["daily_runs"][label] = {
            "completed_at": datetime.now(IST).isoformat(),
            "symbols": len(symbols),
            "alerts": sent,
            "errors": errors,
        }
        save_state(state)
        print(f"SCAN COMPLETE | {label} IST | {len(symbols)} symbols | {sent} alerts | {errors} data errors", flush=True)
        print("=" * 72, flush=True)


async def daily_close_scan(settings: Settings):
    if not settings.telegram_token or not settings.telegram_chat_id:
        raise SystemExit("Scheduled mode requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
    notifier = TelegramNotifier(settings.telegram_token, settings.telegram_chat_id)
    state = load_state()
    access_bot = AccessBot(settings.telegram_token, settings.admin_telegram_id, ())
    access_task = asyncio.create_task(access_bot.run())
    panel = Panel(port=settings.admin_panel_port, password=settings.admin_panel_password, token=settings.telegram_token, pairs=access_bot.pairs)
    threading.Thread(target=panel.start, daemon=True).start()

    # User-requested behavior: scan immediately when the process starts,
    # then continue on the fixed 4-hour schedule anchored at 02:35 IST.
    startup_key = datetime.now(IST).strftime('%Y-%m-%dT%H:%M:%S-startup')
    print("STARTUP SCAN: running immediately before waiting for the next scheduled slot...", flush=True)
    await _run_production_scan(settings, notifier, access_bot, state, startup_key, evaluate_h4_running_scan)

    while True:
        now = datetime.now(IST)
        anchor = now.replace(hour=settings.daily_scan_hour, minute=settings.daily_scan_minute, second=0, microsecond=0)
        if now < anchor:
            target = anchor
        else:
            elapsed = now - anchor
            slots = int(elapsed.total_seconds() // (4 * 3600)) + 1
            target = anchor + timedelta(hours=4 * slots)
        wait_seconds = max(1, (target - now).total_seconds())
        print(f"Next scheduled scan: {target.strftime('%Y-%m-%d %H:%M:%S %Z')} (every 4 hours)", flush=True)
        await asyncio.sleep(wait_seconds)
        run_key = target.strftime('%Y-%m-%dT%H:%M')
        evaluator = evaluate_daily_close_scan if (target.hour == settings.daily_scan_hour and target.minute == settings.daily_scan_minute) else evaluate_h4_running_scan
        await _run_production_scan(settings, notifier, access_bot, state, run_key, evaluator)


async def main():
    settings = Settings.from_env()
    if settings.mt5_login <= 0:
        raise SystemExit("MT5_LOGIN is missing or invalid. Put your demo login in .env")
    if settings.run_mode == "SCHEDULED":
        await daily_close_scan(settings)
    else:
        await audit_once(settings)


if __name__ == "__main__":
    asyncio.run(main())
