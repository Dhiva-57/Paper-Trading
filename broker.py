import os

import config
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    TakeProfitRequest,
    StopLossRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

if not config.PAPER_TRADING or config.ALLOW_LIVE_TRADING:
    raise RuntimeError(
        "SAFETY BLOCK: this project is configured for paper trading only."
    )

client = TradingClient(
    os.environ["APCA_API_KEY_ID"],
    os.environ["APCA_API_SECRET_KEY"],
    paper=True,
)

def get_account():
    return client.get_account()

def get_positions():
    return client.get_all_positions()

def get_clock():
    return client.get_clock()

def buy_bracket(symbol, qty, target_price, stop_price):
    if qty <= 0:
        raise ValueError("Quantity must be positive")

    if stop_price >= target_price:
        raise ValueError("Invalid bracket prices")

    request = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        order_class=OrderClass.BRACKET,
        take_profit=TakeProfitRequest(
            limit_price=round(target_price, 2)
        ),
        stop_loss=StopLossRequest(
            stop_price=round(stop_price, 2)
        ),
    )

    return client.submit_order(request)

def close_position(symbol):
    return client.close_position(symbol)
