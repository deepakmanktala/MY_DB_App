# Zerodha Kite trading agent

This is a production-oriented starter scaffold for Zerodha Kite execution workflows.

## What it does
- Reads your config from YAML
- Connects to Zerodha Kite using your API key + access token
- Places entry orders
- Waits for fills
- Places target and stop-loss exit orders
- Supports:
  - manual entry
  - breakout entry based on live LTP
  - paper mode
  - live mode
  - risk checks
  - WebSocket tick consumption

## What you update
Open `config.yaml.example`, copy it to `config.yaml`, then edit:
- `kite.api_key`
- `kite.access_token`
- `kite.user_id`
- `instrument.exchange`
- `instrument.tradingsymbol`
- `instrument.quantity`
- `instrument.order_type`
- `instrument.transaction_type`
- `instrument.price`
- `strategy.target_price`
- `strategy.stop_loss_price`

## Install
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run
```bash
python zerodha_trading_agent.py config.yaml
```

## Very important
- Start in `paper` mode.
- Do not switch to `live` until you verify every field and order workflow.
- This is an execution engine, not a guaranteed winning strategy.
- Broker/product/order-type rules differ by instrument and segment. Validate with your Zerodha account and exchange rules.

## Likely extensions
- bracket-like orchestration logic in userland
- trailing stop modification logic
- multiple symbols watchlist
- instrument token cache
- persistent audit log / sqlite
- Telegram or email alerts
- daily P&L kill-switch
- end-of-day square-off
- GTT-based exit workflows
