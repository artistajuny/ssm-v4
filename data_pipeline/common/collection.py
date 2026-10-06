from datetime import date, datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

KRX_SOURCE_CODE = "KRX_OPEN_API"


def get_or_create_krx_source_id(
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
            "source_code": KRX_SOURCE_CODE,
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
    collector_name: str,
    dataset_name: str,
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
            "collector_name": collector_name,
            "dataset_name": dataset_name,
            "start_date": start_date,
            "end_date": end_date,
            "run_type": ("INCREMENTAL" if start_date == end_date else "BACKFILL"),
        },
    )

    return result.scalar_one()


def mark_collection_success(
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
                rows_rejected = 0,
                error_message = null
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


def mark_collection_failed(
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
    dataset_name: str,
    last_data_date: date,
    last_available_at: datetime,
) -> None:
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
                :last_data_date,
                :last_available_at,
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
            "dataset_name": dataset_name,
            "last_data_date": last_data_date,
            "last_available_at": last_available_at,
        },
    )
