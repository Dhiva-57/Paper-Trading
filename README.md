# Paper Trading Bot

Paper-only automated US equity day-trading prototype using Alpaca.

## Safety

- `paper=True` is hard-coded in `broker.py`.
- Live trading is disabled in `config.py`.
- Shorting/options/leverage are not implemented.
- Risk is capped per trade and per day.
- Entries use a 15-minute Opening Range Breakout.
- Bracket orders attach stop-loss and take-profit to the entry.
- Positions are flattened at the configured EOD cutoff.
- News headlines can block trades around major catalysts.

## Important limitation

The strategy uses IEX minute data. IEX is not a consolidated SIP feed, so it can have missing bars and different coverage from the full US market. Paper-test and backtest before considering any live deployment.

## Setup

1. Set environment variables in PowerShell:

```powershell
$env:APCA_API_KEY_ID="YOUR_KEY"
$env:APCA_API_SECRET_KEY="YOUR_SECRET"
```

Do not put keys in source files.

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Test the historical replay:

```powershell
python time_machine.py --symbol AAPL --days 30
```

4. Test the scanner:

```powershell
python intraday_scanner.py
```

5. Run the automated paper loop:

```powershell
python main.py
```

Stop with `Ctrl+C`.

## Project flow

Market clock -> 1-minute data -> ORB scanner -> news filter -> entry proposal -> risk engine -> Alpaca paper bracket order -> EOD flatten -> CSV log.

This is a research/paper-trading system, not a profitability guarantee.
