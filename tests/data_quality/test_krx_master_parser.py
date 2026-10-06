from decimal import Decimal

from data_pipeline.collectors.master.krx_master import (
    KRXMasterCollector,
)


def test_parse_decimal_numeric_value() -> None:
    assert KRXMasterCollector._parse_decimal("5,000") == Decimal("5000")


def test_parse_decimal_no_par_value() -> None:
    assert KRXMasterCollector._parse_decimal("무액면") is None


def test_parse_decimal_empty_value() -> None:
    assert KRXMasterCollector._parse_decimal("") is None
