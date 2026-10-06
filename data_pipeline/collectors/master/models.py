from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SecurityMasterRecord:
    ticker: str

    name_ko: str

    data_date: date

    market_code: str
    listing_status: str

    available_at: datetime

    isin: str | None = None

    name_abbr_ko: str | None = None
    name_en: str | None = None

    security_type: str = "STOCK"

    first_listed_date: date | None = None
    final_delisted_date: date | None = None

    source_market_name: str | None = None

    security_group_name: str | None = None
    section_type_name: str | None = None
    stock_certificate_type_name: str | None = None

    par_value: Decimal | None = None

    sector_code: str | None = None
    sector_name: str | None = None

    industry_code: str | None = None
    industry_name: str | None = None

    shares_outstanding: int | None = None
    market_cap: Decimal | None = None
