from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MarketIndexDailyRecord:
    data_date: date

    source_index_class: str
    source_index_name: str

    available_at: datetime

    index_code: str | None = None

    close: Decimal | None = None
    change_value: Decimal | None = None
    change_rate: Decimal | None = None

    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None

    volume: int | None = None
    trading_value: Decimal | None = None
    market_cap: Decimal | None = None
