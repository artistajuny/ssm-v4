from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

from data_pipeline.collectors.stock.models import StockDailyRecord


class StockDailyRepository:
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
                from public.raw_stock_daily
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

    def _load_security_map(
        self,
        *,
        source_id: UUID,
        data_date: date,
    ) -> dict[tuple[str, str], UUID]:
        rows = self.connection.execute(
            text(
                """
                select
                    sm.id,
                    sm.ticker,
                    h.market_code
                from public.security_master_history h
                join public.security_master sm
                  on sm.id = h.security_id
                where h.source_id = :source_id
                  and h.data_date = :data_date
                """
            ),
            {
                "source_id": source_id,
                "data_date": data_date,
            },
        )

        return {
            (
                row.market_code,
                row.ticker,
            ): row.id
            for row in rows
        }

    def save_records(
        self,
        *,
        records: list[StockDailyRecord],
        source_id: UUID,
        collection_run_id: UUID,
    ) -> int:
        security_maps: dict[
            date,
            dict[tuple[str, str], UUID],
        ] = {}

        saved_count = 0

        for record in records:
            if record.data_date not in security_maps:
                security_maps[record.data_date] = self._load_security_map(
                    source_id=source_id,
                    data_date=record.data_date,
                )

            security_id = security_maps[record.data_date].get(
                (
                    record.market_code,
                    record.ticker,
                )
            )

            if security_id is None:
                raise RuntimeError(
                    "Security master mapping not found "
                    f"ticker={record.ticker}, "
                    f"market={record.market_code}, "
                    f"date={record.data_date}"
                )

            self.connection.execute(
                text(
                    """
                    insert into public.raw_stock_daily (
                        security_id,
                        data_date,

                        source_ticker,
                        source_stock_name,
                        source_market_name,
                        source_section_name,

                        open,
                        high,
                        low,
                        close,

                        change_value,
                        change_rate,

                        volume,
                        trading_value,
                        market_cap,
                        shares_outstanding,

                        available_at,
                        collected_at,

                        source_id,
                        collection_run_id
                    )
                    values (
                        :security_id,
                        :data_date,

                        :source_ticker,
                        :source_stock_name,
                        :source_market_name,
                        :source_section_name,

                        :open,
                        :high,
                        :low,
                        :close,

                        :change_value,
                        :change_rate,

                        :volume,
                        :trading_value,
                        :market_cap,
                        :shares_outstanding,

                        :available_at,
                        :collected_at,

                        :source_id,
                        :collection_run_id
                    )
                    on conflict (
                        security_id,
                        data_date,
                        source_id
                    )
                    do update
                    set
                        source_ticker =
                            excluded.source_ticker,
                        source_stock_name =
                            excluded.source_stock_name,
                        source_market_name =
                            excluded.source_market_name,
                        source_section_name =
                            excluded.source_section_name,

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
                        shares_outstanding =
                            excluded.shares_outstanding,

                        available_at =
                            excluded.available_at,
                        collected_at =
                            excluded.collected_at,
                        collection_run_id =
                            excluded.collection_run_id
                    """
                ),
                {
                    "security_id": security_id,
                    "data_date": record.data_date,
                    "source_ticker": record.ticker,
                    "source_stock_name": record.name_ko,
                    "source_market_name": (record.source_market_name),
                    "source_section_name": (record.source_section_name),
                    "open": record.open,
                    "high": record.high,
                    "low": record.low,
                    "close": record.close,
                    "change_value": record.change_value,
                    "change_rate": record.change_rate,
                    "volume": record.volume,
                    "trading_value": (record.trading_value),
                    "market_cap": record.market_cap,
                    "shares_outstanding": (record.shares_outstanding),
                    "available_at": (record.available_at),
                    "collected_at": datetime.now(UTC),
                    "source_id": source_id,
                    "collection_run_id": (collection_run_id),
                },
            )

            saved_count += 1

        return saved_count
