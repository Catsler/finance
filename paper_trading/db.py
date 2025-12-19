from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from paper_trading.time_utils import now_cn


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS account (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  cash REAL NOT NULL,
  total_value REAL NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
  symbol TEXT PRIMARY KEY,
  total_quantity INTEGER NOT NULL,
  available_quantity INTEGER NOT NULL,
  avg_cost REAL NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
  signal_id TEXT PRIMARY KEY,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  client_order_id TEXT PRIMARY KEY,
  broker_order_id TEXT,
  signal_id TEXT,
  symbol TEXT NOT NULL,
  direction TEXT NOT NULL,
  order_type TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  price REAL NOT NULL,
  time_in_force TEXT NOT NULL,
  timeout_seconds INTEGER NOT NULL,
  status TEXT NOT NULL,
  cum_filled_qty INTEGER NOT NULL DEFAULT 0,
  reject_code TEXT,
  reject_reason TEXT,
  expires_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (signal_id) REFERENCES signals(signal_id)
);

CREATE TABLE IF NOT EXISTS fills (
  fill_id TEXT PRIMARY KEY,
  client_order_id TEXT NOT NULL,
  broker_trade_id TEXT,
  broker_order_id TEXT,
  symbol TEXT NOT NULL,
  direction TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  price REAL NOT NULL,
  commission REAL NOT NULL,
  stamp_tax REAL NOT NULL,
  transfer_fee REAL NOT NULL,
  trade_time TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (client_order_id) REFERENCES orders(client_order_id)
);

CREATE TABLE IF NOT EXISTS daily_pnl (
  date TEXT PRIMARY KEY,
  start_value REAL,
  end_value REAL,
  realized_pnl REAL,
  unrealized_pnl REAL,
  commission REAL,
  trades INTEGER,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  related_id TEXT,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


@dataclass
class PaperTradingDB:
    db_path: Path

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._conn = _connect(self.db_path)
        with self._lock:
            self._conn.executescript(SCHEMA_SQL)
            self._ensure_account_row()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _ensure_account_row(self) -> None:
        now = now_cn().isoformat()
        row = self._conn.execute("SELECT id FROM account WHERE id = 1").fetchone()
        if row is None:
            self._conn.execute(
                "INSERT INTO account (id, cash, total_value, updated_at) VALUES (1, ?, ?, ?)",
                (0.0, 0.0, now),
            )
            self._conn.commit()

    def _now(self) -> str:
        return now_cn().isoformat()

    def set_initial_cash_if_empty(self, cash: float) -> None:
        with self._lock:
            row = self._conn.execute("SELECT cash, total_value FROM account WHERE id = 1").fetchone()
            if row and float(row["cash"]) == 0.0 and float(row["total_value"]) == 0.0:
                now = self._now()
                self._conn.execute(
                    "UPDATE account SET cash=?, total_value=?, updated_at=? WHERE id = 1",
                    (cash, cash, now),
                )
                self._conn.commit()

    def get_account(self) -> dict[str, Any]:
        with self._lock:
            row = self._conn.execute("SELECT cash, total_value, updated_at FROM account WHERE id = 1").fetchone()
            return dict(row) if row else {"cash": 0.0, "total_value": 0.0, "updated_at": self._now()}

    def update_account(self, cash: float, total_value: float) -> None:
        with self._lock:
            now = self._now()
            self._conn.execute(
                "UPDATE account SET cash=?, total_value=?, updated_at=? WHERE id = 1",
                (cash, total_value, now),
            )
            self._conn.commit()

    def upsert_position(self, symbol: str, total_qty: int, available_qty: int, avg_cost: float) -> None:
        with self._lock:
            now = self._now()
            self._conn.execute(
                """
                INSERT INTO positions (symbol, total_quantity, available_quantity, avg_cost, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                  total_quantity=excluded.total_quantity,
                  available_quantity=excluded.available_quantity,
                  avg_cost=excluded.avg_cost,
                  updated_at=excluded.updated_at
                """,
                (symbol, total_qty, available_qty, avg_cost, now),
            )
            self._conn.commit()

    def get_position(self, symbol: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT symbol, total_quantity, available_quantity, avg_cost, updated_at FROM positions WHERE symbol=?",
                (symbol,),
            ).fetchone()
            return dict(row) if row else None

    def list_positions(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT symbol, total_quantity, available_quantity, avg_cost, updated_at FROM positions ORDER BY symbol"
            ).fetchall()
            return [dict(r) for r in rows]

    def insert_signal(self, signal_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            now = self._now()
            self._conn.execute(
                "INSERT OR REPLACE INTO signals (signal_id, payload_json, created_at) VALUES (?, ?, ?)",
                (signal_id, json.dumps(payload, ensure_ascii=False), now),
            )
            self._conn.commit()

    def insert_order(self, order: dict[str, Any]) -> None:
        with self._lock:
            now = self._now()
            order = dict(order)
            order.setdefault("created_at", now)
            order.setdefault("updated_at", now)
            self._conn.execute(
                """
                INSERT INTO orders (
                  client_order_id, broker_order_id, signal_id, symbol, direction, order_type,
                  quantity, price, time_in_force, timeout_seconds, status, cum_filled_qty,
                  reject_code, reject_reason, expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order["client_order_id"],
                    order.get("broker_order_id"),
                    order.get("signal_id"),
                    order["symbol"],
                    order["direction"],
                    order["order_type"],
                    int(order["quantity"]),
                    float(order["price"]),
                    order["time_in_force"],
                    int(order["timeout_seconds"]),
                    order["status"],
                    int(order.get("cum_filled_qty", 0)),
                    order.get("reject_code"),
                    order.get("reject_reason"),
                    order.get("expires_at"),
                    order["created_at"],
                    order["updated_at"],
                ),
            )
            self._conn.commit()

    def get_order(self, client_order_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM orders WHERE client_order_id=?", (client_order_id,)).fetchone()
            return dict(row) if row else None

    def list_orders(self, status: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            if status:
                rows = self._conn.execute(
                    "SELECT * FROM orders WHERE status=? ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def update_order_status(
        self,
        client_order_id: str,
        status: str,
        *,
        cum_filled_qty: int | None = None,
        reject_code: str | None = None,
        reject_reason: str | None = None,
    ) -> None:
        with self._lock:
            now = self._now()
            fields = ["status=?", "updated_at=?"]
            params: list[Any] = [status, now]
            if cum_filled_qty is not None:
                fields.append("cum_filled_qty=?")
                params.append(int(cum_filled_qty))
            if reject_code is not None:
                fields.append("reject_code=?")
                params.append(reject_code)
            if reject_reason is not None:
                fields.append("reject_reason=?")
                params.append(reject_reason)
            params.append(client_order_id)
            self._conn.execute(f"UPDATE orders SET {', '.join(fields)} WHERE client_order_id=?", params)
            self._conn.commit()

    def set_order_expires_at(self, client_order_id: str, expires_at: str | None) -> None:
        with self._lock:
            now = self._now()
            self._conn.execute(
                "UPDATE orders SET expires_at=?, updated_at=? WHERE client_order_id=?",
                (expires_at, now, client_order_id),
            )
            self._conn.commit()

    def list_expired_open_orders(self, now_iso: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM orders
                WHERE status='NEW' AND expires_at IS NOT NULL AND expires_at <= ?
                ORDER BY created_at
                """,
                (now_iso,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_open_orders(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM orders WHERE status='NEW' ORDER BY created_at").fetchall()
            return [dict(r) for r in rows]

    def insert_fill(self, fill: dict[str, Any]) -> None:
        with self._lock:
            now = self._now()
            fill = dict(fill)
            fill.setdefault("created_at", now)
            self._conn.execute(
                """
                INSERT INTO fills (
                  fill_id, client_order_id, broker_trade_id, broker_order_id, symbol, direction,
                  quantity, price, commission, stamp_tax, transfer_fee, trade_time, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fill["fill_id"],
                    fill["client_order_id"],
                    fill.get("broker_trade_id"),
                    fill.get("broker_order_id"),
                    fill["symbol"],
                    fill["direction"],
                    int(fill["quantity"]),
                    float(fill["price"]),
                    float(fill["commission"]),
                    float(fill["stamp_tax"]),
                    float(fill["transfer_fee"]),
                    fill["trade_time"],
                    fill["created_at"],
                ),
            )
            self._conn.commit()

    def list_fills(self, since_iso: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
        with self._lock:
            if since_iso:
                rows = self._conn.execute(
                    "SELECT * FROM fills WHERE trade_time >= ? ORDER BY trade_time DESC LIMIT ?",
                    (since_iso, limit),
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM fills ORDER BY trade_time DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def count_trades_for_date(self, date_prefix: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM fills WHERE trade_time LIKE ?",
                (f"{date_prefix}%",),
            ).fetchone()
            return int(row["n"]) if row else 0

    def sum_fees_for_date(self, date_prefix: str) -> float:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT
                  COALESCE(SUM(commission + stamp_tax + transfer_fee), 0) AS fees
                FROM fills
                WHERE trade_time LIKE ?
                """,
                (f"{date_prefix}%",),
            ).fetchone()
            return float(row["fees"]) if row else 0.0

    def upsert_daily_pnl(
        self,
        *,
        date: str,
        start_value: float | None,
        end_value: float | None,
        realized_pnl: float | None,
        unrealized_pnl: float | None,
        commission: float | None,
        trades: int | None,
    ) -> None:
        with self._lock:
            now = self._now()
            self._conn.execute(
                """
                INSERT INTO daily_pnl (
                  date, start_value, end_value, realized_pnl, unrealized_pnl, commission, trades, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                  start_value=excluded.start_value,
                  end_value=excluded.end_value,
                  realized_pnl=excluded.realized_pnl,
                  unrealized_pnl=excluded.unrealized_pnl,
                  commission=excluded.commission,
                  trades=excluded.trades
                """,
                (date, start_value, end_value, realized_pnl, unrealized_pnl, commission, trades, now),
            )
            self._conn.commit()

    def list_daily_pnl(self, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if date_from and date_to:
                rows = self._conn.execute(
                    "SELECT * FROM daily_pnl WHERE date BETWEEN ? AND ? ORDER BY date",
                    (date_from, date_to),
                ).fetchall()
            elif date_from:
                rows = self._conn.execute(
                    "SELECT * FROM daily_pnl WHERE date >= ? ORDER BY date",
                    (date_from,),
                ).fetchall()
            elif date_to:
                rows = self._conn.execute(
                    "SELECT * FROM daily_pnl WHERE date <= ? ORDER BY date",
                    (date_to,),
                ).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM daily_pnl ORDER BY date").fetchall()
            return [dict(r) for r in rows]

    def append_event(self, event_type: str, related_id: str | None, payload: dict[str, Any]) -> int:
        with self._lock:
            now = self._now()
            cur = self._conn.execute(
                "INSERT INTO events (event_type, related_id, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (event_type, related_id, json.dumps(payload, ensure_ascii=False), now),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def list_events(self, since_id: int = 0, limit: int = 500) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, event_type, related_id, payload_json, created_at FROM events WHERE id > ? ORDER BY id LIMIT ?",
                (since_id, limit),
            ).fetchall()
            out: list[dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "id": int(r["id"]),
                        "event_type": r["event_type"],
                        "related_id": r["related_id"],
                        "created_at": r["created_at"],
                        "payload": json.loads(r["payload_json"]),
                    }
                )
            return out

    def get_state(self, key: str) -> str | None:
        with self._lock:
            row = self._conn.execute("SELECT value FROM system_state WHERE key=?", (key,)).fetchone()
            return str(row["value"]) if row else None

    def set_state(self, key: str, value: str) -> None:
        with self._lock:
            now = self._now()
            self._conn.execute(
                """
                INSERT INTO system_state (key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, now),
            )
            self._conn.commit()
