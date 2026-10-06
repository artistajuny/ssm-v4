from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class StockDailyRecord:
    ticker: str
    name_ko: str

    market_code: str
    data_date: date

    available_at: datetime

    source_market_name: str | None = None
    source_section_name: str | None = None

    close: Decimal | None = None
    change_value: Decimal | None = None
    change_rate: Decimal | None = None

    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None

    volume: int | None = None
    trading_value: Decimal | None = None

    market_cap: Decimal | None = None
    shares_outstanding: int | None = None
