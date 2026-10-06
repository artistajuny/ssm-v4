from collections import Counter

from data_pipeline.collectors.stock.models import StockDailyRecord


class StockDailyValidationError(ValueError):
    pass


def validate_stock_daily_records(
    records: list[StockDailyRecord],
) -> None:
    if not records:
        raise StockDailyValidationError("Stock daily collection returned zero records.")

    keys = [
        (
            record.ticker,
            record.data_date,
            record.market_code,
        )
        for record in records
    ]

    duplicates = [key for key, count in Counter(keys).items() if count > 1]

    if duplicates:
        raise StockDailyValidationError(f"Duplicate stock daily keys: {duplicates[:20]}")

    for record in records:
        if record.market_code not in {
            "KOSPI",
            "KOSDAQ",
            "KONEX",
        }:
            raise StockDailyValidationError(f"Invalid market_code={record.market_code}")

        for value_name, value in (
            ("open", record.open),
            ("high", record.high),
            ("low", record.low),
            ("close", record.close),
            ("volume", record.volume),
            ("trading_value", record.trading_value),
            ("market_cap", record.market_cap),
            (
                "shares_outstanding",
                record.shares_outstanding,
            ),
        ):
            if value is not None and value < 0:
                raise StockDailyValidationError(f"{value_name} must be >= 0 ticker={record.ticker}")

        no_trade_day = (
            record.volume == 0
            and record.trading_value == 0
            and record.open == 0
            and record.high == 0
            and record.low == 0
        )

        if no_trade_day:
            continue

        if record.low is not None and record.high is not None and record.low > record.high:
            raise StockDailyValidationError(f"low > high ticker={record.ticker}")

        if (
            record.open is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.open <= record.high)
        ):
            raise StockDailyValidationError(f"open outside OHLC range ticker={record.ticker}")

        if (
            record.close is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.close <= record.high)
        ):
            raise StockDailyValidationError(f"close outside OHLC range ticker={record.ticker}")
