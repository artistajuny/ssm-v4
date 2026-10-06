import argparse
from datetime import date
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

from backend.app.db.session import engine
from data_pipeline.collectors.master.krx_master import KRXMasterCollector
from data_pipeline.collectors.master.repository import SecurityMasterRepository
from data_pipeline.validation.master import validate_security_master_records

SOURCE_CODE = "KRX_OPEN_API"
DATASET_NAME = "security_master"


def parse_date(
    value: str,
) -> date:
    return date.fromisoformat(value)


def get_or_create_source_id(
    connection: Connection,
) -> UUID:
    result = connection.execute(
        text(
            """
            insert into public.data_sources (
                source_code,
                source_name,
                source_type,
                base_url,
                timezone,
                is_active
            )
            values (
                :source_code,
                :source_name,
                :source_type,
                :base_url,
                :timezone,
                true
            )
            on conflict (source_code)
            do update
            set
                source_name = excluded.source_name,
                source_type = excluded.source_type,
                base_url = excluded.base_url,
                timezone = excluded.timezone,
                is_active = true,
                updated_at = now()
            returning id
            """
        ),
        {
            "source_code": SOURCE_CODE,
            "source_name": "KRX Open API",
            "source_type": "OPEN_API",
            "base_url": "https://data-dbg.krx.co.kr",
            "timezone": "Asia/Seoul",
        },
    )

    return result.scalar_one()


def create_collection_run(
    connection: Connection,
    *,
    source_id: UUID,
    start_date: date,
    end_date: date,
) -> UUID:
    result = connection.execute(
        text(
            """
            insert into public.collection_runs (
                source_id,
                collector_name,
                dataset_name,
                start_date,
                end_date,
                run_type,
                status,
                started_at
            )
            values (
                :source_id,
                :collector_name,
                :dataset_name,
                :start_date,
                :end_date,
                :run_type,
                'RUNNING',
                now()
            )
            returning id
            """
        ),
        {
            "source_id": source_id,
            "collector_name": "KRXMasterCollector",
            "dataset_name": DATASET_NAME,
            "start_date": start_date,
            "end_date": end_date,
            "run_type": ("INCREMENTAL" if start_date == end_date else "BACKFILL"),
        },
    )

    return result.scalar_one()


def mark_run_success(
    connection: Connection,
    *,
    run_id: UUID,
    rows_received: int,
    rows_inserted: int,
    rows_updated: int,
) -> None:
    connection.execute(
        text(
            """
            update public.collection_runs
            set
                status = 'SUCCESS',
                finished_at = now(),
                rows_received = :rows_received,
                rows_inserted = :rows_inserted,
                rows_updated = :rows_updated,
                rows_rejected = 0
            where id = :run_id
            """
        ),
        {
            "run_id": run_id,
            "rows_received": rows_received,
            "rows_inserted": rows_inserted,
            "rows_updated": rows_updated,
        },
    )


def mark_run_failed(
    connection: Connection,
    *,
    run_id: UUID,
    error_message: str,
) -> None:
    connection.execute(
        text(
            """
            update public.collection_runs
            set
                status = 'FAILED',
                finished_at = now(),
                error_message = :error_message
            where id = :run_id
            """
        ),
        {
            "run_id": run_id,
            "error_message": error_message[:5000],
        },
    )


def update_watermark(
    connection: Connection,
    *,
    source_id: UUID,
    records,
) -> None:
    if not records:
        return

    last_data_date = max(record.data_date for record in records)

    last_available_at = max(record.available_at for record in records)

    connection.execute(
        text(
            """
            insert into public.ingestion_watermarks (
                source_id,
                dataset_name,
                last_success_data_date,
                last_success_available_at,
                last_success_collected_at
            )
            values (
                :source_id,
                :dataset_name,
                :last_success_data_date,
                :last_success_available_at,
                now()
            )
            on conflict (
                source_id,
                dataset_name
            )
            do update
            set
                last_success_data_date =
                    excluded.last_success_data_date,
                last_success_available_at =
                    excluded.last_success_available_at,
                last_success_collected_at = now(),
                updated_at = now()
            """
        ),
        {
            "source_id": source_id,
            "dataset_name": DATASET_NAME,
            "last_success_data_date": last_data_date,
            "last_success_available_at": last_available_at,
        },
    )


def collect_security_master(
    *,
    start_date: date,
    end_date: date,
) -> None:
    collector = KRXMasterCollector()

    with engine.begin() as connection:
        source_id = get_or_create_source_id(connection)

        run_id = create_collection_run(
            connection,
            source_id=source_id,
            start_date=start_date,
            end_date=end_date,
        )

    try:
        records = collector.collect(
            start_date=start_date,
            end_date=end_date,
        )

        validate_security_master_records(records)

        with engine.begin() as connection:
            repository = SecurityMasterRepository(connection)

            before_count = repository.count_history_rows(
                source_id=source_id,
                start_date=start_date,
                end_date=end_date,
            )

            saved_count = repository.save_records(
                records=records,
                source_id=source_id,
                collection_run_id=run_id,
            )

            after_count = repository.count_history_rows(
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

            update_watermark(
                connection,
                source_id=source_id,
                records=records,
            )

            mark_run_success(
                connection,
                run_id=run_id,
                rows_received=len(records),
                rows_inserted=inserted_count,
                rows_updated=updated_count,
            )

        print("Security master collection completed.")
        print(f"start_date={start_date}")
        print(f"end_date={end_date}")
        print(f"received_count={len(records)}")
        print(f"inserted_count={inserted_count}")
        print(f"updated_count={updated_count}")

    except Exception as exc:
        with engine.begin() as connection:
            mark_run_failed(
                connection,
                run_id=run_id,
                error_message=str(exc),
            )

        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=("Collect KRX security master data."))

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

    collect_security_master(
        start_date=args.start_date,
        end_date=args.end_date,
    )


if __name__ == "__main__":
    main()
