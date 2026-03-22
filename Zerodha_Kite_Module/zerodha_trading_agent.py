#!/usr/bin/env python3
"""
Zerodha Kite execution agent
----------------------------
Purpose:
- Consume user-provided trade instructions
- Optionally connect to Zerodha Kite live market data
- Place, modify, and cancel orders with strong safety checks
- Track fills and optionally place target / stop-loss exit orders
- Default to PAPER mode for safety

This is an execution/risk-control scaffold, not a profit-guaranteeing strategy.
Read the README and test in PAPER mode first.
"""

from __future__ import annotations

import json
import logging
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import yaml
except Exception:
    yaml = None

try:
    from kiteconnect import KiteConnect, KiteTicker
except Exception:
    KiteConnect = None
    KiteTicker = None


# -------------------- Logging --------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("zerodha-agent")


# -------------------- Config models --------------------

@dataclass
class KiteCfg:
    api_key: str
    access_token: str
    user_id: str = ""


@dataclass
class InstrumentCfg:
    exchange: str
    tradingsymbol: str
    quantity: int
    product: str = "CNC"
    order_type: str = "LIMIT"
    transaction_type: str = "BUY"
    variety: str = "regular"
    validity: str = "DAY"
    price: Optional[float] = None
    trigger_price: Optional[float] = None


@dataclass
class RiskCfg:
    mode: str = "paper"  # paper | live
    max_order_value: float = 100000.0
    max_daily_loss: float = 5000.0
    max_position_qty: int = 100
    max_trades_per_day: int = 10
    dry_run_exit_orders: bool = False
    require_limit_price_for_entry: bool = True
    square_off_on_shutdown: bool = False


@dataclass
class StrategyCfg:
    entry_mode: str = "manual"  # manual | breakout_ltp
    entry_above_ltp: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    trailing_sl_points: Optional[float] = None
    poll_interval_seconds: float = 1.0
    use_websocket_ticks: bool = True


@dataclass
class AppCfg:
    kite: KiteCfg
    instrument: InstrumentCfg
    risk: RiskCfg
    strategy: StrategyCfg


# -------------------- Helpers --------------------

def load_yaml(path: str) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is not installed. Install requirements.txt first.")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def as_cfg(raw: Dict[str, Any]) -> AppCfg:
    return AppCfg(
        kite=KiteCfg(**raw["kite"]),
        instrument=InstrumentCfg(**raw["instrument"]),
        risk=RiskCfg(**raw.get("risk", {})),
        strategy=StrategyCfg(**raw.get("strategy", {})),
    )


def clamp_positive(name: str, value: Optional[float]) -> None:
    if value is None:
        return
    if value <= 0:
        raise ValueError(f"{name} must be > 0")


def pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


# -------------------- Broker wrapper --------------------

class ZerodhaBroker:
    def __init__(self, cfg: AppCfg):
        self.cfg = cfg
        self.kite = None
        self.ticker = None
        self.connected = False
        self.ltp_cache: Dict[str, float] = {}
        self.tick_lock = threading.Lock()
        self._shutdown = False

        if KiteConnect is None:
            raise RuntimeError(
                "kiteconnect package not found. Install requirements.txt first."
            )

        self.kite = KiteConnect(api_key=cfg.kite.api_key)
        self.kite.set_access_token(cfg.kite.access_token)

    @property
    def instrument_key(self) -> str:
        i = self.cfg.instrument
        return f"{i.exchange}:{i.tradingsymbol}"

    def get_ltp(self) -> float:
        data = self.kite.ltp([self.instrument_key])
        ltp = float(data[self.instrument_key]["last_price"])
        with self.tick_lock:
            self.ltp_cache[self.instrument_key] = ltp
        return ltp

    def place_order(self, **kwargs) -> str:
        order_id = self.kite.place_order(**kwargs)
        log.info("Placed order: %s", order_id)
        return order_id

    def modify_order(self, variety: str, order_id: str, **kwargs) -> Any:
        return self.kite.modify_order(variety=variety, order_id=order_id, **kwargs)

    def cancel_order(self, variety: str, order_id: str) -> Any:
        return self.kite.cancel_order(variety=variety, order_id=order_id)

    def orders(self) -> List[Dict[str, Any]]:
        return self.kite.orders()

    def order_history(self, order_id: str) -> List[Dict[str, Any]]:
        return self.kite.order_history(order_id)

    def trades(self) -> List[Dict[str, Any]]:
        return self.kite.trades()

    def instruments(self, exchange: Optional[str] = None):
        return self.kite.instruments(exchange=exchange)

    def find_instrument_token(self, exchange: str, tradingsymbol: str) -> Optional[int]:
        rows = self.instruments(exchange=exchange)
        for row in rows:
            if row.get("tradingsymbol") == tradingsymbol:
                return int(row["instrument_token"])
        return None

    def start_ws(self, on_tick):
        if not self.cfg.strategy.use_websocket_ticks:
            return
        if KiteTicker is None:
            log.warning("KiteTicker unavailable; continuing without websocket.")
            return

        token = self.find_instrument_token(
            self.cfg.instrument.exchange, self.cfg.instrument.tradingsymbol
        )
        if token is None:
            log.warning("Could not resolve instrument token; continuing without websocket.")
            return

        kws = KiteTicker(self.cfg.kite.api_key, self.cfg.kite.access_token)

        def _on_connect(ws, response):
            self.connected = True
            log.info("WebSocket connected. Subscribing to %s", token)
            ws.subscribe([token])
            ws.set_mode(ws.MODE_FULL, [token])

        def _on_ticks(ws, ticks):
            for t in ticks:
                last_price = t.get("last_price")
                if last_price is not None:
                    with self.tick_lock:
                        self.ltp_cache[self.instrument_key] = float(last_price)
                    on_tick(float(last_price), t)

        def _on_close(ws, code, reason):
            self.connected = False
            log.warning("WebSocket closed: code=%s reason=%s", code, reason)

        def _on_error(ws, code, reason):
            self.connected = False
            log.error("WebSocket error: code=%s reason=%s", code, reason)

        kws.on_connect = _on_connect
        kws.on_ticks = _on_ticks
        kws.on_close = _on_close
        kws.on_error = _on_error

        self.ticker = kws
        thread = threading.Thread(target=kws.connect, kwargs={"threaded": False}, daemon=True)
        thread.start()

    def stop(self):
        self._shutdown = True
        if self.ticker:
            try:
                self.ticker.stop()
            except Exception as e:
                log.warning("Ticker stop warning: %s", e)


# -------------------- Risk manager --------------------

class RiskManager:
    def __init__(self, cfg: AppCfg):
        self.cfg = cfg
        self.trade_count = 0
        self.realized_pnl = 0.0

    def preflight(self):
        i = self.cfg.instrument
        r = self.cfg.risk
        clamp_positive("quantity", i.quantity)
        if i.price is not None:
            clamp_positive("price", i.price)
        if i.trigger_price is not None:
            clamp_positive("trigger_price", i.trigger_price)

        if i.quantity > r.max_position_qty:
            raise ValueError(
                f"Quantity {i.quantity} exceeds max_position_qty {r.max_position_qty}"
            )

        if self.trade_count >= r.max_trades_per_day:
            raise RuntimeError("Max trades per day reached")

        if r.require_limit_price_for_entry and i.order_type.upper() == "LIMIT" and not i.price:
            raise ValueError("Entry order_type=LIMIT requires instrument.price")

        approx_price = i.price if i.price else 0
        approx_value = approx_price * i.quantity
        if approx_price and approx_value > r.max_order_value:
            raise ValueError(
                f"Approx order value {approx_value} exceeds limit {r.max_order_value}"
            )

        if abs(self.realized_pnl) >= r.max_daily_loss and self.realized_pnl < 0:
            raise RuntimeError("Daily loss limit already breached")

    def on_trade(self):
        self.trade_count += 1


# -------------------- Order / execution manager --------------------

class ExecutionAgent:
    def __init__(self, cfg: AppCfg):
        self.cfg = cfg
        self.broker = ZerodhaBroker(cfg)
        self.risk = RiskManager(cfg)
        self._running = True
        self._entry_order_id: Optional[str] = None
        self._exit_order_ids: List[str] = []
        self._entry_filled_price: Optional[float] = None
        self._last_ltp: Optional[float] = None

    def paper_or_live(self) -> str:
        return self.cfg.risk.mode.strip().lower()

    def on_tick(self, ltp: float, raw_tick: Dict[str, Any]):
        self._last_ltp = ltp

    def wait_for_entry_signal(self):
        s = self.cfg.strategy
        i = self.cfg.instrument

        if s.entry_mode == "manual":
            log.info("Manual mode: placing entry immediately.")
            return True

        if s.entry_mode == "breakout_ltp":
            if s.entry_above_ltp is None:
                raise ValueError("strategy.entry_above_ltp must be set for breakout_ltp")
            log.info("Waiting for LTP >= %.2f for %s", s.entry_above_ltp, i.tradingsymbol)
            while self._running:
                ltp = self._last_ltp or self.broker.get_ltp()
                if ltp >= s.entry_above_ltp:
                    log.info("Entry condition met. LTP=%.2f", ltp)
                    return True
                time.sleep(max(0.2, s.poll_interval_seconds))
        else:
            raise ValueError(f"Unsupported strategy.entry_mode: {s.entry_mode}")

        return False

    def build_entry_order(self) -> Dict[str, Any]:
        i = self.cfg.instrument
        order = dict(
            variety=i.variety,
            exchange=i.exchange,
            tradingsymbol=i.tradingsymbol,
            transaction_type=i.transaction_type.upper(),
            quantity=i.quantity,
            product=i.product,
            order_type=i.order_type.upper(),
            validity=i.validity,
        )
        if i.price is not None:
            order["price"] = i.price
        if i.trigger_price is not None:
            order["trigger_price"] = i.trigger_price
        return order

    def place_entry(self):
        self.risk.preflight()
        payload = self.build_entry_order()
        log.info("Entry payload:\n%s", pretty(payload))

        if self.paper_or_live() == "paper":
            fake_id = f"PAPER-{int(time.time())}"
            self._entry_order_id = fake_id
            self._entry_filled_price = self.cfg.instrument.price or self.broker.get_ltp()
            self.risk.on_trade()
            log.warning("PAPER mode: simulated entry order %s at %.2f", fake_id, self._entry_filled_price)
            return fake_id

        order_id = self.broker.place_order(**payload)
        self._entry_order_id = order_id
        self.risk.on_trade()
        return order_id

    def wait_for_fill(self, timeout_seconds: int = 60):
        if self.paper_or_live() == "paper":
            return self._entry_filled_price

        start = time.time()
        while time.time() - start < timeout_seconds and self._running:
            hist = self.broker.order_history(self._entry_order_id)
            latest = hist[-1] if hist else {}
            status = latest.get("status", "")
            avg_price = latest.get("average_price")
            log.info("Entry order status=%s avg_price=%s", status, avg_price)

            if status == "COMPLETE":
                self._entry_filled_price = float(avg_price or 0)
                return self._entry_filled_price
            if status in {"CANCELLED", "REJECTED"}:
                raise RuntimeError(f"Entry order {status}: {pretty(latest)}")

            time.sleep(1.0)

        raise TimeoutError("Entry order not filled within timeout")

    def _exit_side(self) -> str:
        return "SELL" if self.cfg.instrument.transaction_type.upper() == "BUY" else "BUY"

    def place_exit_orders(self):
        s = self.cfg.strategy
        i = self.cfg.instrument

        if s.target_price is None and s.stop_loss_price is None:
            log.info("No exit orders configured.")
            return

        exit_side = self._exit_side()

        if s.target_price is not None:
            target_payload = dict(
                variety=i.variety,
                exchange=i.exchange,
                tradingsymbol=i.tradingsymbol,
                transaction_type=exit_side,
                quantity=i.quantity,
                product=i.product,
                order_type="LIMIT",
                validity=i.validity,
                price=s.target_price,
            )
            self._submit_exit("TARGET", target_payload)

        if s.stop_loss_price is not None:
            sl_payload = dict(
                variety=i.variety,
                exchange=i.exchange,
                tradingsymbol=i.tradingsymbol,
                transaction_type=exit_side,
                quantity=i.quantity,
                product=i.product,
                order_type="SL",
                validity=i.validity,
                price=s.stop_loss_price,
                trigger_price=s.stop_loss_price,
            )
            self._submit_exit("STOP_LOSS", sl_payload)

    def _submit_exit(self, kind: str, payload: Dict[str, Any]):
        log.info("%s payload:\n%s", kind, pretty(payload))
        if self.paper_or_live() == "paper" or self.cfg.risk.dry_run_exit_orders:
            fake_id = f"PAPER-{kind}-{int(time.time())}"
            self._exit_order_ids.append(fake_id)
            log.warning("%s simulated: %s", kind, fake_id)
            return

        order_id = self.broker.place_order(**payload)
        self._exit_order_ids.append(order_id)
        log.info("%s placed: %s", kind, order_id)

    def monitor_trailing_sl(self):
        s = self.cfg.strategy
        if s.trailing_sl_points is None or self._entry_filled_price is None:
            return

        i = self.cfg.instrument
        side = i.transaction_type.upper()
        trail = float(s.trailing_sl_points)
        best_price = self._entry_filled_price

        log.info("Starting trailing stop monitor with trail %.2f", trail)

        while self._running:
            ltp = self._last_ltp or self.broker.get_ltp()

            if side == "BUY":
                best_price = max(best_price, ltp)
                new_sl = best_price - trail
                log.info("Trail BUY | ltp=%.2f best=%.2f new_sl=%.2f", ltp, best_price, new_sl)
            else:
                best_price = min(best_price, ltp)
                new_sl = best_price + trail
                log.info("Trail SELL | ltp=%.2f best=%.2f new_sl=%.2f", ltp, best_price, new_sl)

            time.sleep(max(0.5, s.poll_interval_seconds))

    def run(self):
        log.info("Starting Zerodha execution agent in %s mode", self.paper_or_live())
        log.info("Symbol: %s:%s qty=%s",
                 self.cfg.instrument.exchange,
                 self.cfg.instrument.tradingsymbol,
                 self.cfg.instrument.quantity)

        self.broker.start_ws(self.on_tick)

        if not self.wait_for_entry_signal():
            return

        self.place_entry()
        fill_price = self.wait_for_fill()
        log.info("Entry filled price: %.2f", fill_price)
        self.place_exit_orders()

        if self.cfg.strategy.trailing_sl_points is not None:
            self.monitor_trailing_sl()

    def shutdown(self):
        self._running = False
        try:
            self.broker.stop()
        finally:
            log.info("Agent stopped.")


# -------------------- CLI --------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python zerodha_trading_agent.py config.yaml")
        sys.exit(1)

    cfg = as_cfg(load_yaml(sys.argv[1]))
    agent = ExecutionAgent(cfg)

    def _handle_signal(signum, frame):
        log.warning("Signal received: %s", signum)
        agent.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    agent.run()


if __name__ == "__main__":
    main()
