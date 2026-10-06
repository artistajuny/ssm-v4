from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from backend.app.core.config import settings
from data_pipeline.collectors.market.models import (
    MarketIndexDailyRecord,
)
from data_pipeline.common.krx import (
    clean_text,
    parse_decimal,
    parse_int,
    parse_krx_date,
)


class KRXMarketIndexDailyCollector:
    URLS = {
        "KOSPI": ("https://data-dbg.krx.co.kr/svc/apis/idx/kospi_dd_trd"),
        "KOSDAQ": ("https://data-dbg.krx.co.kr/svc/apis/idx/kosdaq_dd_trd"),
    }

    CORE_INDEX_CODES = {
        ("KOSPI", "코스피"): "KOSPI",
        ("KOSPI", "코스피 200"): "KOSPI200",
        ("KOSDAQ", "코스닥"): "KOSDAQ",
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
    ) -> list[MarketIndexDailyRecord]:
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        records: list[MarketIndexDailyRecord] = []

        current_date = start_date

        while current_date <= end_date:
            if current_date.weekday() < 5:
                records.extend(self.collect_date(current_date))

            current_date += timedelta(days=1)

        return records

    def collect_date(
        self,
        data_date: date,
    ) -> list[MarketIndexDailyRecord]:
        records: list[MarketIndexDailyRecord] = []

        for expected_class, url in self.URLS.items():
            records.extend(
                self._request_family(
                    expected_class=expected_class,
                    url=url,
                    data_date=data_date,
                )
            )

        return records

    def _request_family(
        self,
        *,
        expected_class: str,
        url: str,
        data_date: date,
    ) -> list[MarketIndexDailyRecord]:
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
                f"KRX index response missing OutBlock_1 class={expected_class} date={data_date}"
            )

        if not isinstance(raw_records, list):
            raise RuntimeError("KRX index OutBlock_1 must be list.")

        available_at = datetime.now(UTC)

        return [
            self._parse_record(
                item=item,
                expected_class=expected_class,
                available_at=available_at,
            )
            for item in raw_records
        ]

    def _parse_record(
        self,
        *,
        item: dict[str, Any],
        expected_class: str,
        available_at: datetime,
    ) -> MarketIndexDailyRecord:
        data_date = parse_krx_date(item.get("BAS_DD"))

        source_index_class = clean_text(item.get("IDX_CLSS"))

        source_index_name = clean_text(item.get("IDX_NM"))

        if data_date is None:
            raise RuntimeError("KRX index missing BAS_DD.")

        if source_index_class is None:
            source_index_class = expected_class

        if source_index_name is None:
            raise RuntimeError("KRX index missing IDX_NM.")

        index_code = self.CORE_INDEX_CODES.get(
            (
                source_index_class,
                source_index_name,
            )
        )

        return MarketIndexDailyRecord(
            data_date=data_date,
            source_index_class=source_index_class,
            source_index_name=source_index_name,
            available_at=available_at,
            index_code=index_code,
            close=parse_decimal(item.get("CLSPRC_IDX")),
            change_value=parse_decimal(item.get("CMPPREVDD_IDX")),
            change_rate=parse_decimal(item.get("FLUC_RT")),
            open=parse_decimal(item.get("OPNPRC_IDX")),
            high=parse_decimal(item.get("HGPRC_IDX")),
            low=parse_decimal(item.get("LWPRC_IDX")),
            volume=parse_int(item.get("ACC_TRDVOL")),
            trading_value=parse_decimal(item.get("ACC_TRDVAL")),
            market_cap=parse_decimal(item.get("MKTCAP")),
        )
