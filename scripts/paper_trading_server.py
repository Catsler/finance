#!/usr/bin/env python3
"""
MVP1: Paper Trading backend server (FastAPI + SQLite)

Run:
  pip install -r requirements_paper_trading.txt
  python scripts/paper_trading_server.py --reload
"""

from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Paper Trading API (MVP1)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "paper_trading.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()

