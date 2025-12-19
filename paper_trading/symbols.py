from __future__ import annotations

import re
from dataclasses import dataclass


SYMBOL_RE = re.compile(r"^(?P<code>\d{6})\.(?P<market>SZ|SH)$")


class SymbolError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedSymbol:
    code: str
    market: str  # "SZ" | "SH"
    board: str  # "MAIN" | "CHINEXT"

    @property
    def symbol(self) -> str:
        return f"{self.code}.{self.market}"


def parse_symbol(symbol: str) -> ParsedSymbol:
    match = SYMBOL_RE.match(symbol)
    if not match:
        raise SymbolError("symbol must match like '000001.SZ' or '600519.SH'")

    code = match.group("code")
    market = match.group("market")

    # MVP1: include Main board + ChiNext; exclude STAR/others (we gate by prefixes).
    if code.startswith(("300", "301")):
        board = "CHINEXT"
    elif code.startswith("688"):
        raise SymbolError("科创板暂不支持（MVP1）")
    else:
        board = "MAIN"

    return ParsedSymbol(code=code, market=market, board=board)


def tick_round(price: float) -> float:
    # A-share typical tick size is 0.01; keep it simple for MVP1.
    return round(price + 1e-12, 2)

