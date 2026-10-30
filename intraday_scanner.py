from datetime import time
import pandas as pd

import config
from data import get_bars
from alpaca.data.timeframe import TimeFrame

MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)

def get_intraday_data(symbol, days=3):
    data = get_bars(symbol, days=days, timeframe=TimeFrame.Minute)
    if data is None or data.empty:
        return None

    data = data.reset_index()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    data["timestamp"] = data["timestamp"].dt.tz_convert("America/New_York")

    data = data[
        (data["timestamp"].dt.time >= MARKET_OPEN) &
        (data["timestamp"].dt.time < MARKET_CLOSE)
    ].copy()
    return data

def find_orb_setup(symbol):
    data = get_intraday_data(symbol)
    if data is None or data.empty:
        return None

    latest_date = data["timestamp"].dt.date.max()
    data = data[data["timestamp"].dt.date == latest_date].copy()

    opening_end = pd.Timestamp(
        f"{latest_date} 09:45:00",
        tz="America/New_York"
    )

    opening = data[data["timestamp"] < opening_end]
    after = data[data["timestamp"] >= opening_end]

    if len(opening) < 5 or after.empty:
        return None

    opening_high = float(opening["high"].max())
    opening_low = float(opening["low"].min())

    latest = after.iloc[-1]
    price = float(latest["close"])
    avg_volume = float(opening["volume"].mean())

    if avg_volume <= 0:
        return None

    volume_ratio = float(latest["volume"]) / avg_volume
    breakout = price > opening_high
    volume_ok = volume_ratio >= config.MIN_VOLUME_RATIO

    if not (breakout and volume_ok):
        return None

    return {
        "symbol": symbol,
        "signal": "LONG_SETUP",
        "price": price,
        "opening_high": opening_high,
        "opening_low": opening_low,
        "volume_ratio": volume_ratio,
        "timestamp": latest["timestamp"],
    }

def scan_market():
    setups = []
    for symbol in config.WATCHLIST:
        try:
            setup = find_orb_setup(symbol)
            if setup:
                setups.append(setup)
        except Exception as e:
            print(f"{symbol}: scanner error -> {e}")
    setups.sort(key=lambda x: x["volume_ratio"], reverse=True)
    return setups

if __name__ == "__main__":
    for s in scan_market():
        print(
            f"{s['symbol']} LONG_SETUP "
            f"price=${s['price']:.2f} "
            f"OR_high=${s['opening_high']:.2f} "
            f"OR_low=${s['opening_low']:.2f} "
            f"volume={s['volume_ratio']:.2f}x"
        )
