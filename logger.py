import csv
import os
from datetime import datetime, timezone

LOG_FILE = os.path.join(
    os.path.dirname(__file__),
    "trader",
    "trades.csv",
)

def log_event(event, symbol="", details=""):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["timestamp", "event", "symbol", "details"])

        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            event,
            symbol,
            details,
        ])
