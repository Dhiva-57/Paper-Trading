from data import get_bars
from alpaca.data.timeframe import TimeFrame

def build_entry(setup):
    symbol = setup["symbol"]
    data = get_bars(symbol, days=3, timeframe=TimeFrame.Minute)

    if data is None or data.empty:
        return None

    data = data.reset_index()
    recent = data.tail(20)

    # Conservative stop: opening-range low.
    entry = float(setup["price"])
    stop = float(setup["opening_low"])

    # Use a minimum stop distance to avoid absurdly tight stops.
    recent_range = float((recent["high"] - recent["low"]).median())
    minimum_distance = max(recent_range, entry * 0.002)

    if entry - stop < minimum_distance:
        stop = entry - minimum_distance

    risk_per_share = entry - stop
    target = entry + 2.0 * risk_per_share

    if stop <= 0 or risk_per_share <= 0:
        return None

    return {
        **setup,
        "entry": entry,
        "stop": stop,
        "target": target,
        "risk_per_share": risk_per_share,
        "reward_risk": 2.0,
    }
