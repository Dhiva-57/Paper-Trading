import time
from datetime import datetime
from zoneinfo import ZoneInfo

import config
from broker import get_clock, get_positions, close_position
from logger import log_event

NY = ZoneInfo("America/New_York")

def run_once():
    clock = get_clock()
    now = clock.timestamp.astimezone(NY)

    # Always flatten before the configured EOD cutoff.
    if (now.hour, now.minute) >= (
        config.EOD_EXIT_HOUR,
        config.EOD_EXIT_MINUTE,
    ):
        positions = get_positions()
        for position in positions:
            symbol = position.symbol
            try:
                close_position(symbol)
                log_event("EOD_EXIT", symbol, "Closed before end of session")
                print(f"EOD EXIT: {symbol}")
            except Exception as e:
                log_event("EOD_EXIT_ERROR", symbol, str(e))
                print(f"EOD EXIT ERROR {symbol}: {e}")

def run_forever():
    print("Position monitor running...")
    while True:
        try:
            run_once()
        except Exception as e:
            print("Monitor error:", e)
        time.sleep(config.SCAN_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_forever()
