from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from backend.app.core.config import settings
from data_pipeline.collectors.master.base import SecurityMasterCollector
from data_pipeline.collectors.master.models import SecurityMasterRecord


class KRXMasterCollector(SecurityMasterCollector):
    BASE_URLS = {
        "KOSPI": "https://data-dbg.krx.co.kr/svc/apis/sto/stk_isu_base_info",
        "KOSDAQ": "https://data-dbg.krx.co.kr/svc/apis/sto/ksq_isu_base_info",
        "KONEX": "https://data-dbg.krx.co.kr/svc/apis/sto/knx_isu_base_info",
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
    ) -> list[SecurityMasterRecord]:
        if start_date > end_date:
            raise ValueError("start_date must be less than or equal to end_date.")

        records: list[SecurityMasterRecord] = []

        current_date = start_date

        while current_date <= end_date:
            records.extend(self.collect_date(current_date))

            current_date = date.fromordinal(current_date.toordinal() + 1)

        return records

    def collect_date(
        self,
        data_date: date,
    ) -> list[SecurityMasterRecord]:
        records: list[SecurityMasterRecord] = []

        for market_code, url in self.BASE_URLS.items():
            market_records = self._request_market(
                market_code=market_code,
                url=url,
                data_date=data_date,
            )

            records.extend(market_records)

        return records

    def _request_market(
        self,
        *,
        market_code: str,
        url: str,
        data_date: date,
    ) -> list[SecurityMasterRecord]:
        params = {
            "basDd": data_date.strftime("%Y%m%d"),
        }

        headers = {
            "AUTH_KEY": self.api_key,
        }

        with httpx.Client(
            timeout=self.timeout_seconds,
        ) as client:
            response = client.get(
                url,
                params=params,
                headers=headers,
            )

        response.raise_for_status()

        payload = response.json()

        raw_records = payload.get("OutBlock_1")

        if raw_records is None:
            raise RuntimeError(
                "KRX response does not contain OutBlock_1 "
                f"market={market_code}, "
                f"data_date={data_date}"
            )

        if not isinstance(raw_records, list):
            raise RuntimeError(
                f"KRX OutBlock_1 must be a list market={market_code}, data_date={data_date}"
            )

        available_at = datetime.now(UTC)

        return [
            self._parse_record(
                item=item,
                market_code=market_code,
                data_date=data_date,
                available_at=available_at,
            )
            for item in raw_records
        ]

    def _parse_record(
        self,
        *,
        item: dict[str, Any],
        market_code: str,
        data_date: date,
        available_at: datetime,
    ) -> SecurityMasterRecord:
        ticker = self._clean_text(item.get("ISU_SRT_CD"))

        isin = self._clean_text(item.get("ISU_CD"))

        name_ko = self._clean_text(item.get("ISU_NM"))

        if not ticker:
            raise RuntimeError("KRX record has empty ISU_SRT_CD.")

        if not isin:
            raise RuntimeError(f"KRX record has empty ISU_CD ticker={ticker}")

        if not name_ko:
            raise RuntimeError(f"KRX record has empty ISU_NM ticker={ticker}")

        return SecurityMasterRecord(
            ticker=ticker,
            isin=isin,
            name_ko=name_ko,
            name_abbr_ko=self._clean_text(item.get("ISU_ABBRV")),
            name_en=self._clean_text(item.get("ISU_ENG_NM")),
            data_date=data_date,
            market_code=market_code,
            listing_status="LISTED",
            available_at=available_at,
            security_type="STOCK",
            first_listed_date=self._parse_date(item.get("LIST_DD")),
            final_delisted_date=None,
            source_market_name=self._clean_text(item.get("MKT_TP_NM")),
            security_group_name=self._clean_text(item.get("SECUGRP_NM")),
            section_type_name=self._clean_text(item.get("SECT_TP_NM")),
            stock_certificate_type_name=self._clean_text(item.get("KIND_STKCERT_TP_NM")),
            par_value=self._parse_decimal(item.get("PARVAL")),
            sector_code=None,
            sector_name=None,
            industry_code=None,
            industry_name=None,
            shares_outstanding=self._parse_int(item.get("LIST_SHRS")),
            market_cap=None,
        )

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        return text

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> date | None:
        text = KRXMasterCollector._clean_text(value)

        if text is None:
            return None

        formats = (
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y%m%d",
        )

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                ).date()
            except ValueError:
                continue

        raise RuntimeError(f"Unsupported KRX date format: {text}")

    @staticmethod
    def _parse_int(
        value: Any,
    ) -> int | None:
        text = KRXMasterCollector._clean_text(value)

        if text is None:
            return None

        normalized = text.replace(",", "")

        try:
            return int(Decimal(normalized))
        except (
            InvalidOperation,
            ValueError,
        ) as exc:
            raise RuntimeError(f"Invalid integer value from KRX: {text}") from exc

    @staticmethod
    def _parse_decimal(
        value: Any,
    ) -> Decimal | None:
        text = KRXMasterCollector._clean_text(value)

        if text is None:
            return None

        if text in {
            "무액면",
            "해당없음",
            "-",
        }:
            return None

        normalized = text.replace(",", "")

        try:
            return Decimal(normalized)
        except InvalidOperation as exc:
            raise RuntimeError(f"Invalid decimal value from KRX: {text}") from exc
