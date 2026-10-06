from datetime import UTC, date, datetime
from decimal import Decimal

from data_pipeline.collectors.market.krx_index_daily import (
    KRXMarketIndexDailyCollector,
)
from data_pipeline.collectors.stock.krx_stock_daily import (
    KRXStockDailyCollector,
)


def test_stock_daily_parse_record() -> None:
    collector = object.__new__(KRXStockDailyCollector)

    record = collector._parse_record(
        item={
            "BAS_DD": "20261001",
            "ISU_CD": "005930",
            "ISU_NM": "삼성전자",
            "MKT_NM": "KOSPI",
            "SECT_TP_NM": "",
            "TDD_CLSPRC": "70,000",
            "CMPPREVDD_PRC": "1,000",
            "FLUC_RT": "1.45",
            "TDD_OPNPRC": "69,000",
            "TDD_HGPRC": "71,000",
            "TDD_LWPRC": "68,500",
            "ACC_TRDVOL": "1000000",
            "ACC_TRDVAL": "70000000000",
            "MKTCAP": "400000000000000",
            "LIST_SHRS": "5969782550",
        },
        market_code="KOSPI",
        available_at=datetime.now(UTC),
    )

    assert record.ticker == "005930"
    assert record.data_date == date(2026, 10, 1)
    assert record.close == Decimal("70000")
    assert record.volume == 1000000


def test_market_index_parse_blank_values() -> None:
    collector = object.__new__(KRXMarketIndexDailyCollector)

    record = collector._parse_record(
        item={
            "BAS_DD": "20200414",
            "IDX_CLSS": "KOSPI",
            "IDX_NM": "코스피200제외 코스피지수",
            "CLSPRC_IDX": "2183.24",
            "CMPPREVDD_IDX": "41.38",
            "FLUC_RT": "1.93",
            "OPNPRC_IDX": "",
            "HGPRC_IDX": "",
            "LWPRC_IDX": "",
            "ACC_TRDVOL": "",
            "ACC_TRDVAL": "",
            "MKTCAP": "",
        },
        expected_class="KOSPI",
        available_at=datetime.now(UTC),
    )

    assert record.close == Decimal("2183.24")
    assert record.open is None
    assert record.volume is None
