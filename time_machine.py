"""
Simple historical replay for the 15-minute ORB idea.

This is a research tool, not a guarantee of future performance.
It uses available IEX minute bars and models entry at the first
bar close above the opening high, with a 2R target and opening-low stop.
"""

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from data import get_bars

NY = ZoneInfo("America/New_York")

def backtest(symbol, days=30):
    data = get_bars(symbol, days=days, timeframe=__import__(
        "alpaca.data.timeframe", fromlist=["TimeFrame"]
    ).TimeFrame.Minute)

    if data is None or data.empty:
        return {"trades": 0, "wins": 0, "losses": 0, "pnl_r": 0.0}

    data = data.reset_index()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True).dt.tz_convert(NY)
    data = data[
        (data["timestamp"].dt.hour > 9) |
        ((data["timestamp"].dt.hour == 9) & (data["timestamp"].dt.minute >= 30))
    ]
    data = data[data["timestamp"].dt.hour < 16]

    total = wins = losses = 0
    pnl_r = 0.0

    for day, day_df in data.groupby(data["timestamp"].dt.date):
        opening_end = pd.Timestamp(f"{day} 09:45:00", tz=NY)
        opening = day_df[day_df["timestamp"] < opening_end]
        after = day_df[day_df["timestamp"] >= opening_end]

        if len(opening) < 5 or after.empty:
            continue

        or_high = float(opening["high"].max())
        or_low = float(opening["low"].min())
        risk = None

        for _, bar in after.iterrows():
            entry = float(bar["close"])

            if risk is None and entry > or_high:
                risk = entry - or_low
                if risk <= 0:
                    risk = None
                    continue

                total += 1
                target = entry + 2 * risk

                # Conservative same-bar assumption: if both are touched,
                # count the stop first to avoid optimistic backtests.
                future = after[after["timestamp"] >= bar["timestamp"]]

                outcome = None
                for _, future_bar in future.iterrows():
                    if float(future_bar["low"]) <= or_low:
                        outcome = -1.0
                        break
                    if float(future_bar["high"]) >= target:
                        outcome = 2.0
                        break

                if outcome is None:
                    outcome = 0.0

                pnl_r += outcome
                if outcome > 0:
                    wins += 1
                elif outcome < 0:
                    losses += 1

                break

    win_rate = wins / total if total else 0.0
    return {
        "trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "pnl_r": pnl_r,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    result = backtest(args.symbol, args.days)
    print(result)
