from collections import Counter

from data_pipeline.collectors.market.models import (
    MarketIndexDailyRecord,
)


class MarketIndexValidationError(ValueError):
    pass


def validate_market_index_daily_records(
    records: list[MarketIndexDailyRecord],
) -> None:
    if not records:
        raise MarketIndexValidationError("Market index collection returned zero records.")

    keys = [
        (
            record.source_index_class,
            record.source_index_name,
            record.data_date,
        )
        for record in records
    ]

    duplicates = [key for key, count in Counter(keys).items() if count > 1]

    if duplicates:
        raise MarketIndexValidationError(f"Duplicate market index rows: {duplicates[:20]}")

    for record in records:
        if not record.source_index_class:
            raise MarketIndexValidationError("source_index_class is required.")

        if not record.source_index_name:
            raise MarketIndexValidationError("source_index_name is required.")

        for value_name, value in (
            ("open", record.open),
            ("high", record.high),
            ("low", record.low),
            ("close", record.close),
            ("volume", record.volume),
            ("trading_value", record.trading_value),
            ("market_cap", record.market_cap),
        ):
            if value is not None and value < 0:
                raise MarketIndexValidationError(
                    f"{value_name} must be >= 0 index={record.source_index_name}"
                )

        if record.low is not None and record.high is not None and record.low > record.high:
            raise MarketIndexValidationError(f"low > high index={record.source_index_name}")
