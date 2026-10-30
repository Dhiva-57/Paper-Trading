from data import get_bars


def analyze_stock(symbol):
    data = get_bars(symbol, days=120)

    if len(data) < 50:
        return {
            "symbol": symbol,
            "signal": "NO TRADE",
            "reason": "Not enough historical data"
        }

    close = data["close"]
    volume = data["volume"]

    current_price = close.iloc[-1]

    # Moving averages
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    # Daily momentum
    previous_price = close.iloc[-2]

    daily_change = (
        (current_price - previous_price)
        / previous_price
    ) * 100

    # Recent volume
    average_volume = volume.iloc[-20:].mean()
    current_volume = volume.iloc[-1]

    volume_ratio = current_volume / average_volume

    # Trend
    if current_price > ma20 and ma20 > ma50:
        trend = "BULLISH"

    elif current_price < ma20 and ma20 < ma50:
        trend = "BEARISH"

    else:
        trend = "NEUTRAL"

    # Strategy decision
    signal = "NO TRADE"
    reason = "Conditions not strong enough"

    if (
        trend == "BULLISH"
        and daily_change > 1
        and volume_ratio > 1.2
    ):
        signal = "WATCH BUY"
        reason = "Bullish trend + momentum + strong volume"

    elif (
        trend == "BEARISH"
        and daily_change < -1
        and volume_ratio > 1.2
    ):
        signal = "WATCH"
        reason = "Bearish trend + strong downside momentum"

    return {
        "symbol": symbol,
        "price": current_price,
        "trend": trend,
        "daily_change": daily_change,
        "volume_ratio": volume_ratio,
        "ma20": ma20,
        "ma50": ma50,
        "signal": signal,
        "reason": reason
    }


if __name__ == "__main__":

    WATCHLIST = [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "META",
        "TSLA",
        "AMD",
        "GOOGL"
    ]

    print("\nStrategy Analysis\n")
    print("-" * 75)

    for symbol in WATCHLIST:

        try:
            result = analyze_stock(symbol)

            print(
                f"{result['symbol']:6} "
                f"{result['signal']:10} "
                f"Trend: {result.get('trend', 'N/A'):8} "
                f"Change: {result.get('daily_change', 0):+.2f}% "
                f"Volume: {result.get('volume_ratio', 0):.2f}x"
            )

        except Exception as e:

            print(
                f"{symbol}: error -> {e}"
            )