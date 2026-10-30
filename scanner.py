from data import get_bars


WATCHLIST = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "TSLA",
    "AMD",
    "GOOGL",
]


def scan_stock(symbol):
    data = get_bars(symbol, days=120)

    if len(data) < 20:
        return None

    # Latest and previous close
    current_close = data["close"].iloc[-1]
    previous_close = data["close"].iloc[-2]

    # Daily percentage change
    change_percent = (
        (current_close - previous_close)
        / previous_close
    ) * 100

    # 20-day average volume
    average_volume = data["volume"].iloc[-20:].mean()

    current_volume = data["volume"].iloc[-1]

    volume_ratio = current_volume / average_volume

    return {
        "symbol": symbol,
        "price": current_close,
        "change_percent": change_percent,
        "volume_ratio": volume_ratio,
    }


def scan_market():
    candidates = []

    for symbol in WATCHLIST:
        try:
            result = scan_stock(symbol)

            if result:
                candidates.append(result)

        except Exception as e:
            print(f"{symbol}: error -> {e}")

    candidates.sort(
        key=lambda x: x["change_percent"],
        reverse=True
    )

    return candidates


if __name__ == "__main__":

    print("\nMarket Scanner\n")
    print("-" * 60)

    results = scan_market()

    for stock in results:
        print(
            f"{stock['symbol']:6} "
            f"Price: ${stock['price']:.2f}  "
            f"Change: {stock['change_percent']:+.2f}%  "
            f"Volume: {stock['volume_ratio']:.2f}x"
        )