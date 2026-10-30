import time
from zoneinfo import ZoneInfo

import config
from broker import (
    get_account,
    get_clock,
    get_positions,
    buy_bracket,
    close_position,
)
from intraday_scanner import scan_market
from entry import build_entry
from news import has_major_catalyst
from risk import (
    ensure_day,
    risk_check,
    daily_limits_ok,
    record_trade,
)
from logger import log_event


NY = ZoneInfo("America/New_York")


def already_holding(symbol):
    return any(
        position.symbol == symbol
        for position in get_positions()
    )


def close_all_positions():
    """Close all open positions before the end of the session."""

    positions = get_positions()

    if not positions:
        print("No open positions.")
        return

    for position in positions:
        symbol = position.symbol

        try:
            close_position(symbol)

            print(f"EOD EXIT: {symbol}")

            log_event(
                "EOD_EXIT",
                symbol,
                "Position closed before market close"
            )

        except Exception as e:

            print(
                f"EOD EXIT ERROR: {symbol} -> {e}"
            )

            log_event(
                "EOD_EXIT_ERROR",
                symbol,
                str(e)
            )


def main_loop():

    print("=== PAPER DAY TRADER ===")
    print("Live trading: DISABLED")
    print("Shorting: DISABLED")
    print("Options: DISABLED")
    print()

    while True:

        try:

            # ---------------------------------
            # MARKET CLOCK
            # ---------------------------------

            clock = get_clock()

            now = clock.timestamp.astimezone(NY)

            account = get_account()

            equity = float(account.equity)

            ensure_day(equity)


            # ---------------------------------
            # MARKET STATUS
            # ---------------------------------

            if not clock.is_open:

                # Before market open
                if now.time() < clock.next_open.astimezone(NY).time():

                    next_open = clock.next_open.astimezone(NY)

                    print(
                        f"PRE-MARKET | "
                        f"Now: {now.strftime('%Y-%m-%d %H:%M:%S')} ET | "
                        f"Market opens: {next_open.strftime('%H:%M:%S')} ET"
                    )

                # After market close
                else:

                    next_open = clock.next_open.astimezone(NY)

                    print(
                        f"AFTER-HOURS | "
                        f"Market closed at {now.strftime('%H:%M:%S')} ET | "
                        f"Next open: {next_open.strftime('%Y-%m-%d %H:%M:%S')} ET"
                    )

                time.sleep(config.SCAN_INTERVAL_SECONDS)

                continue


            # ---------------------------------
            # MARKET IS OPEN
            # ---------------------------------

            print(
                f"MARKET OPEN | "
                f"{now.strftime('%Y-%m-%d %H:%M:%S')} ET"
            )


            # ---------------------------------
            # EOD EXIT
            # ---------------------------------

            if (
                now.hour > config.EOD_EXIT_HOUR
                or (
                    now.hour == config.EOD_EXIT_HOUR
                    and now.minute >= config.EOD_EXIT_MINUTE
                )
            ):

                print("EOD cutoff reached.")

                close_all_positions()

                print("Trading finished for today.")

                # Wait until next market session
                time.sleep(300)

                continue


            # ---------------------------------
            # WAIT FOR OPENING RANGE
            # ---------------------------------

            opening_range_end_minutes = (
                9 * 60
                + 30
                + config.OPENING_RANGE_MINUTES
            )

            current_minutes = (
                now.hour * 60
                + now.minute
            )

            if current_minutes < opening_range_end_minutes:

                print(
                    "Waiting for opening range..."
                )

                time.sleep(
                    config.SCAN_INTERVAL_SECONDS
                )

                continue


            # ---------------------------------
            # ENTRY CUTOFF
            # ---------------------------------

            if (
                now.hour > config.ENTRY_CUTOFF_HOUR
                or (
                    now.hour == config.ENTRY_CUTOFF_HOUR
                    and now.minute > config.ENTRY_CUTOFF_MINUTE
                )
            ):

                print(
                    "Entry window closed. "
                    "Monitoring existing positions."
                )

                time.sleep(
                    config.SCAN_INTERVAL_SECONDS
                )

                continue


            # ---------------------------------
            # DAILY RISK CHECK
            # ---------------------------------

            allowed, reason = daily_limits_ok(
                equity
            )

            if not allowed:

                print(
                    f"RISK BLOCK: {reason}"
                )

                time.sleep(
                    config.SCAN_INTERVAL_SECONDS
                )

                continue


            # ---------------------------------
            # SCAN MARKET
            # ---------------------------------

            print("Scanning market...")

            setups = scan_market()

            if not setups:

                print(
                    "No valid setups."
                )

                time.sleep(
                    config.SCAN_INTERVAL_SECONDS
                )

                continue


            # ---------------------------------
            # PROCESS SETUPS
            # ---------------------------------

            for setup in setups:

                symbol = setup["symbol"]


                # Already holding?
                if already_holding(symbol):

                    print(
                        f"{symbol}: already holding"
                    )

                    continue


                # ---------------------------------
                # NEWS FILTER
                # ---------------------------------

                try:

                    catalyst, headline = (
                        has_major_catalyst(symbol)
                    )

                except Exception as e:

                    print(
                        f"{symbol}: news check failed -> {e}"
                    )

                    log_event(
                        "NEWS_ERROR",
                        symbol,
                        str(e)
                    )

                    # Safety-first:
                    # don't trade if news check fails.
                    continue


                if catalyst:

                    print(
                        f"{symbol}: blocked by news catalyst"
                    )

                    log_event(
                        "NEWS_BLOCK",
                        symbol,
                        headline or ""
                    )

                    continue


                # ---------------------------------
                # BUILD ENTRY
                # ---------------------------------

                proposal = build_entry(setup)

                if not proposal:

                    continue


                # ---------------------------------
                # RISK CHECK
                # ---------------------------------

                allowed, result = risk_check(
                    equity,
                    proposal["entry"],
                    proposal["stop"],
                    proposal["target"],
                )

                if not allowed:

                    print(
                        f"{symbol}: "
                        f"RISK BLOCK -> {result}"
                    )

                    log_event(
                        "RISK_BLOCK",
                        symbol,
                        str(result)
                    )

                    continue


                qty = result["quantity"]


                # ---------------------------------
                # FINAL SAFETY CHECK
                # ---------------------------------

                if not config.PAPER_TRADING:

                    raise RuntimeError(
                        "SAFETY BLOCK: "
                        "Paper trading must remain enabled."
                    )


                if config.ALLOW_LIVE_TRADING:

                    raise RuntimeError(
                        "SAFETY BLOCK: "
                        "Live trading is disabled."
                    )


                if config.ALLOW_SHORTING:

                    raise RuntimeError(
                        "SAFETY BLOCK: "
                        "Shorting is disabled."
                    )


                # ---------------------------------
                # PAPER ORDER
                # ---------------------------------

                print()
                print(
                    "PAPER BUY"
                )

                print(
                    f"Symbol: {symbol}"
                )

                print(
                    f"Quantity: {qty}"
                )

                print(
                    f"Entry: ${proposal['entry']:.2f}"
                )

                print(
                    f"Stop: ${proposal['stop']:.2f}"
                )

                print(
                    f"Target: ${proposal['target']:.2f}"
                )

                print(
                    f"R:R: "
                    f"{proposal['reward_risk']:.2f}:1"
                )


                try:

                    order = buy_bracket(
                        symbol,
                        qty,
                        proposal["target"],
                        proposal["stop"],
                    )

                except Exception as e:

                    print(
                        f"ORDER ERROR: "
                        f"{symbol} -> {e}"
                    )

                    log_event(
                        "ORDER_ERROR",
                        symbol,
                        str(e)
                    )

                    continue


                # ---------------------------------
                # RECORD TRADE
                # ---------------------------------

                record_trade(symbol)

                log_event(
                    "BUY_BRACKET",
                    symbol,
                    (
                        f"order={order.id}; "
                        f"qty={qty}; "
                        f"entry={proposal['entry']}; "
                        f"stop={proposal['stop']}; "
                        f"target={proposal['target']}"
                    )
                )

                print(
                    f"Paper order submitted: "
                    f"{order.id}"
                )

                # Only one new trade per scan.
                break


        except KeyboardInterrupt:

            print(
                "\nBot stopped by user."
            )

            break


        except Exception as e:

            print(
                f"MAIN LOOP ERROR: {e}"
            )

            log_event(
                "ERROR",
                "",
                str(e)
            )


        time.sleep(
            config.SCAN_INTERVAL_SECONDS
        )


if __name__ == "__main__":
    main_loop()