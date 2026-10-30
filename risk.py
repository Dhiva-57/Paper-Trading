import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import config

STATE_FILE = os.path.join(os.path.dirname(__file__), "trader", "state.json")
NY = ZoneInfo("America/New_York")

def _load_state():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def ensure_day(account_equity):
    state = _load_state()
    today = datetime.now(NY).date().isoformat()
    if state.get("date") != today:
        state = {
            "date": today,
            "start_equity": float(account_equity),
            "trades": 0,
            "symbols_traded": [],
        }
        _save_state(state)
    return state

def record_trade(symbol):
    state = _load_state()
    state["trades"] = int(state.get("trades", 0)) + 1
    state.setdefault("symbols_traded", []).append(symbol)
    _save_state(state)

def daily_loss_pct(account_equity):
    state = _load_state()
    start = float(state.get("start_equity", account_equity))
    if start <= 0:
        return 0.0
    return max(0.0, (start - float(account_equity)) / start)

def risk_check(account_equity, entry_price, stop_price, target_price):
    if entry_price <= 0 or stop_price <= 0 or target_price <= 0:
        return False, "Invalid price"

    if stop_price >= entry_price:
        return False, "For a long trade, stop must be below entry"

    if target_price <= entry_price:
        return False, "For a long trade, target must be above entry"

    rr = (target_price - entry_price) / (entry_price - stop_price)
    if rr < config.MIN_REWARD_RISK:
        return False, f"Reward/Risk below {config.MIN_REWARD_RISK}:1"

    risk_amount = float(account_equity) * config.MAX_RISK_PER_TRADE
    risk_per_share = entry_price - stop_price
    qty = int(risk_amount / risk_per_share)

    if qty <= 0:
        return False, "Position size is zero"

    notional = qty * entry_price
    return True, {
        "quantity": qty,
        "risk_amount": qty * risk_per_share,
        "risk_per_share": risk_per_share,
        "reward_per_share": target_price - entry_price,
        "reward_risk": rr,
        "notional": notional,
    }

def daily_limits_ok(account_equity):
    state = ensure_day(account_equity)
    if state["trades"] >= config.MAX_TRADES_PER_DAY:
        return False, "Maximum daily trade count reached"

    loss = daily_loss_pct(account_equity)
    if loss >= config.MAX_DAILY_LOSS:
        return False, "Maximum daily loss reached"

    return True, {
        "trades": state["trades"],
        "daily_loss_pct": loss,
    }
