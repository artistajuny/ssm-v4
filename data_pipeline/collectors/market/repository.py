from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

from data_pipeline.collectors.market.models import (
    MarketIndexDailyRecord,
)


class MarketIndexDailyRepository:
    def __init__(
        self,
        connection: Connection,
    ) -> None:
        self.connection = connection

    def count_rows(
        self,
        *,
        source_id: UUID,
        start_date: date,
        end_date: date,
    ) -> int:
        result = self.connection.execute(
            text(
                """
                select count(*)
                from public.raw_market_index_daily
                where source_id = :source_id
                  and data_date between :start_date and :end_date
                """
            ),
            {
                "source_id": source_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        return int(result.scalar_one())

    def save_records(
        self,
        *,
        records: list[MarketIndexDailyRecord],
        source_id: UUID,
        collection_run_id: UUID,
    ) -> int:
        saved_count = 0

        for record in records:
            self.connection.execute(
                text(
                    """
                    insert into public.raw_market_index_daily (
                        index_code,

                        source_index_class,
                        source_index_name,

                        data_date,

                        open,
                        high,
                        low,
                        close,

                        change_value,
                        change_rate,

                        volume,
                        trading_value,
                        market_cap,

                        available_at,
                        collected_at,

                        source_id,
                        collection_run_id
                    )
                    values (
                        :index_code,

                        :source_index_class,
                        :source_index_name,

                        :data_date,

                        :open,
                        :high,
                        :low,
                        :close,

                        :change_value,
                        :change_rate,

                        :volume,
                        :trading_value,
                        :market_cap,

                        :available_at,
                        :collected_at,

                        :source_id,
                        :collection_run_id
                    )
                    on conflict (
                        source_index_class,
                        source_index_name,
                        data_date,
                        source_id
                    )
                    do update
                    set
                        index_code =
                            excluded.index_code,

                        open = excluded.open,
                        high = excluded.high,
                        low = excluded.low,
                        close = excluded.close,

                        change_value =
                            excluded.change_value,
                        change_rate =
                            excluded.change_rate,

                        volume = excluded.volume,
                        trading_value =
                            excluded.trading_value,
                        market_cap =
                            excluded.market_cap,

                        available_at =
                            excluded.available_at,
                        collected_at =
                            excluded.collected_at,
                        collection_run_id =
                            excluded.collection_run_id
                    """
                ),
                {
                    "index_code": record.index_code,
                    "source_index_class": (record.source_index_class),
                    "source_index_name": (record.source_index_name),
                    "data_date": record.data_date,
                    "open": record.open,
                    "high": record.high,
                    "low": record.low,
                    "close": record.close,
                    "change_value": record.change_value,
                    "change_rate": record.change_rate,
                    "volume": record.volume,
                    "trading_value": (record.trading_value),
                    "market_cap": record.market_cap,
                    "available_at": (record.available_at),
                    "collected_at": datetime.now(UTC),
                    "source_id": source_id,
                    "collection_run_id": (collection_run_id),
                },
            )

            saved_count += 1

        return saved_count
