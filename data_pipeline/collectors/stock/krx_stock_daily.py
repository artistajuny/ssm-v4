from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from backend.app.core.config import settings
from data_pipeline.collectors.stock.models import StockDailyRecord
from data_pipeline.common.krx import (
    clean_text,
    parse_decimal,
    parse_int,
    parse_krx_date,
)


class KRXStockDailyCollector:
    URLS = {
        "KOSPI": ("https://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd"),
        "KOSDAQ": ("https://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd"),
        "KONEX": ("https://data-dbg.krx.co.kr/svc/apis/sto/knx_bydd_trd"),
    }

    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not settings.krx_api_key:
            raise RuntimeError("KRX_API_KEY is not configured.")

        self.api_key = settings.krx_api_key
        self.timeout_seconds = timeout_seconds

    def collect(
        self,
        start_date: date,
        end_date: date,
    ) -> list[StockDailyRecord]:
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        records: list[StockDailyRecord] = []

        current_date = start_date

        while current_date <= end_date:
            if current_date.weekday() < 5:
                records.extend(self.collect_date(current_date))

            current_date += timedelta(days=1)

        return records

    def collect_date(
        self,
        data_date: date,
    ) -> list[StockDailyRecord]:
        records: list[StockDailyRecord] = []

        for market_code, url in self.URLS.items():
            records.extend(
                self._request_market(
                    market_code=market_code,
                    url=url,
                    data_date=data_date,
                )
            )

        return records

    def _request_market(
        self,
        *,
        market_code: str,
        url: str,
        data_date: date,
    ) -> list[StockDailyRecord]:
        headers = {
            "AUTH_KEY": self.api_key,
        }

        params = {
            "basDd": data_date.strftime("%Y%m%d"),
        }

        with httpx.Client(
            timeout=self.timeout_seconds,
        ) as client:
            response = client.get(
                url,
                headers=headers,
                params=params,
            )

        response.raise_for_status()

        payload = response.json()

        raw_records = payload.get("OutBlock_1")

        if raw_records is None:
            raise RuntimeError(
                f"KRX response missing OutBlock_1 market={market_code} date={data_date}"
            )

        if not isinstance(raw_records, list):
            raise RuntimeError("KRX OutBlock_1 must be list.")

        available_at = datetime.now(UTC)

        return [
            self._parse_record(
                item=item,
                market_code=market_code,
                available_at=available_at,
            )
            for item in raw_records
        ]

    def _parse_record(
        self,
        *,
        item: dict[str, Any],
        market_code: str,
        available_at: datetime,
    ) -> StockDailyRecord:
        ticker = clean_text(item.get("ISU_CD"))

        name_ko = clean_text(item.get("ISU_NM"))

        data_date = parse_krx_date(item.get("BAS_DD"))

        if ticker is None:
            raise RuntimeError("KRX stock daily missing ISU_CD.")

        if name_ko is None:
            raise RuntimeError(f"KRX stock daily missing ISU_NM ticker={ticker}")

        if data_date is None:
            raise RuntimeError(f"KRX stock daily missing BAS_DD ticker={ticker}")

        return StockDailyRecord(
            ticker=ticker,
            name_ko=name_ko,
            market_code=market_code,
            data_date=data_date,
            available_at=available_at,
            source_market_name=clean_text(item.get("MKT_NM")),
            source_section_name=clean_text(item.get("SECT_TP_NM")),
            close=parse_decimal(item.get("TDD_CLSPRC")),
            change_value=parse_decimal(item.get("CMPPREVDD_PRC")),
            change_rate=parse_decimal(item.get("FLUC_RT")),
            open=parse_decimal(item.get("TDD_OPNPRC")),
            high=parse_decimal(item.get("TDD_HGPRC")),
            low=parse_decimal(item.get("TDD_LWPRC")),
            volume=parse_int(item.get("ACC_TRDVOL")),
            trading_value=parse_decimal(item.get("ACC_TRDVAL")),
            market_cap=parse_decimal(item.get("MKTCAP")),
            shares_outstanding=parse_int(item.get("LIST_SHRS")),
        )
