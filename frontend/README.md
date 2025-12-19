# Stock Trading Dashboard

React + Vite frontend for Paper Trading monitoring and execution.

## Features (v0.1)

- 📊 **Watchlist**: Monitor Top 5 stocks with live prices
- 💹 **Trading Panel**: Place BUY/SELL orders (AGGRESSIVE/LIMIT)
- 🛡️ **Kill Switch**: Emergency stop for all trading
- 📋 **Orders/Fills**: Real-time order status and execution history
- 🔄 **Auto Polling**: Quotes (2s) / Account (5s)

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Dependencies

- React 18
- Ant Design 5
- ECharts (v0.2+)
- Zustand (state management)
- Axios (API client)

## Backend Requirement

Paper Trading server must be running on http://127.0.0.1:8000

```bash
python3 scripts/paper_trading_server.py
```

## Roadmap

- v0.1: ✅ Watchlist, Trading, Orders/Fills
- v0.2: 📈 K-line chart + KDJ indicators
- v0.3: 🔌 WebSocket + 5-level orderbook
