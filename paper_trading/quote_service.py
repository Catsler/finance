from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from paper_trading.models import Quote
from paper_trading.time_utils import parse_quote_timestamp
from utils.realtime_quote import get_realtime_quotes


@dataclass(frozen=True)
class QuoteService:
    quote_cache_seconds: int

    def fetch_quotes(self, symbols: Iterable[str]) -> dict[str, Quote]:
        symbols_list = list(dict.fromkeys(symbols))
        if not symbols_list:
            return {}

        raw_quotes = get_realtime_quotes(symbols_list, cache_seconds=self.quote_cache_seconds)
        out: dict[str, Quote] = {}
        for raw in raw_quotes:
            qt = parse_quote_timestamp(raw.get("timestamp", ""))
            try:
                quote = Quote.model_validate({**raw, "quote_time": qt})
            except Exception:
                continue
            out[quote.symbol] = quote
        return out

