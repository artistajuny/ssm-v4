import argparse
from datetime import date

from backend.app.db.session import engine
from data_pipeline.collectors.market.krx_index_daily import (
    KRXMarketIndexDailyCollector,
)
from data_pipeline.collectors.market.repository import (
    MarketIndexDailyRepository,
)
from data_pipeline.common.collection import (
    create_collection_run,
    get_or_create_krx_source_id,
    mark_collection_failed,
    mark_collection_success,
    update_watermark,
)
from data_pipeline.validation.market_index_daily import (
    validate_market_index_daily_records,
)

DATASET_NAME = "raw_market_index_daily"


def parse_date(
    value: str,
) -> date:
    return date.fromisoformat(value)


def collect_market_index_daily(
    *,
    start_date: date,
    end_date: date,
) -> None:
    collector = KRXMarketIndexDailyCollector()

    with engine.begin() as connection:
        source_id = get_or_create_krx_source_id(connection)

        run_id = create_collection_run(
            connection,
            source_id=source_id,
            collector_name=("KRXMarketIndexDailyCollector"),
            dataset_name=DATASET_NAME,
            start_date=start_date,
            end_date=end_date,
        )

    try:
        records = collector.collect(
            start_date=start_date,
            end_date=end_date,
        )

        validate_market_index_daily_records(records)

        with engine.begin() as connection:
            repository = MarketIndexDailyRepository(connection)

            before_count = repository.count_rows(
                source_id=source_id,
                start_date=start_date,
                end_date=end_date,
            )

            saved_count = repository.save_records(
                records=records,
                source_id=source_id,
                collection_run_id=run_id,
            )

            after_count = repository.count_rows(
                source_id=source_id,
                start_date=start_date,
                end_date=end_date,
            )

            inserted_count = max(
                after_count - before_count,
                0,
            )

            updated_count = max(
                saved_count - inserted_count,
                0,
            )

            last_data_date = max(record.data_date for record in records)

            last_available_at = max(record.available_at for record in records)

            update_watermark(
                connection,
                source_id=source_id,
                dataset_name=DATASET_NAME,
                last_data_date=last_data_date,
                last_available_at=last_available_at,
            )

            mark_collection_success(
                connection,
                run_id=run_id,
                rows_received=len(records),
                rows_inserted=inserted_count,
                rows_updated=updated_count,
            )

        print("Market index collection completed.")
        print(f"received_count={len(records)}")
        print(f"inserted_count={inserted_count}")
        print(f"updated_count={updated_count}")

    except Exception as exc:
        with engine.begin() as connection:
            mark_collection_failed(
                connection,
                run_id=run_id,
                error_message=str(exc),
            )

        raise


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start-date",
        required=True,
        type=parse_date,
    )

    parser.add_argument(
        "--end-date",
        required=True,
        type=parse_date,
    )

    args = parser.parse_args()

    collect_market_index_daily(
        start_date=args.start_date,
        end_date=args.end_date,
    )


if __name__ == "__main__":
    main()
