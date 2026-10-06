from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Connection

from data_pipeline.collectors.master.models import SecurityMasterRecord


class SecurityMasterRepository:
    def __init__(
        self,
        connection: Connection,
    ) -> None:
        self.connection = connection

    def upsert_security(
        self,
        record: SecurityMasterRecord,
    ) -> UUID:
        if not record.isin:
            raise ValueError("ISIN is required when saving security master records.")

        result = self.connection.execute(
            text(
                """
                insert into public.security_master (
                    ticker,
                    isin,
                    name_ko,
                    name_abbr_ko,
                    name_en,
                    security_type,
                    first_listed_date,
                    final_delisted_date
                )
                values (
                    :ticker,
                    :isin,
                    :name_ko,
                    :name_abbr_ko,
                    :name_en,
                    :security_type,
                    :first_listed_date,
                    :final_delisted_date
                )
                on conflict (isin)
                where isin is not null
                do update
                set
                    ticker = excluded.ticker,
                    name_ko = excluded.name_ko,
                    name_abbr_ko = excluded.name_abbr_ko,
                    name_en = coalesce(
                        excluded.name_en,
                        security_master.name_en
                    ),
                    security_type = excluded.security_type,
                    first_listed_date = coalesce(
                        security_master.first_listed_date,
                        excluded.first_listed_date
                    ),
                    final_delisted_date = coalesce(
                        excluded.final_delisted_date,
                        security_master.final_delisted_date
                    ),
                    updated_at = now()
                returning id
                """
            ),
            {
                "ticker": record.ticker,
                "isin": record.isin,
                "name_ko": record.name_ko,
                "name_abbr_ko": record.name_abbr_ko,
                "name_en": record.name_en,
                "security_type": record.security_type,
                "first_listed_date": record.first_listed_date,
                "final_delisted_date": record.final_delisted_date,
            },
        )

        return result.scalar_one()

    def upsert_history(
        self,
        *,
        security_id: UUID,
        record: SecurityMasterRecord,
        source_id: UUID,
        collection_run_id: UUID | None,
    ) -> None:
        collected_at = datetime.now(UTC)

        self.connection.execute(
            text(
                """
                insert into public.security_master_history (
                    security_id,
                    data_date,
                    market_code,
                    listing_status,

                    source_market_name,
                    security_group_name,
                    section_type_name,
                    stock_certificate_type_name,
                    par_value,

                    sector_code,
                    sector_name,
                    industry_code,
                    industry_name,

                    shares_outstanding,
                    market_cap,

                    available_at,
                    collected_at,

                    source_id,
                    collection_run_id
                )
                values (
                    :security_id,
                    :data_date,
                    :market_code,
                    :listing_status,

                    :source_market_name,
                    :security_group_name,
                    :section_type_name,
                    :stock_certificate_type_name,
                    :par_value,

                    :sector_code,
                    :sector_name,
                    :industry_code,
                    :industry_name,

                    :shares_outstanding,
                    :market_cap,

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
                    market_code =
                        excluded.market_code,

                    listing_status =
                        excluded.listing_status,

                    source_market_name =
                        excluded.source_market_name,

                    security_group_name =
                        excluded.security_group_name,

                    section_type_name =
                        excluded.section_type_name,

                    stock_certificate_type_name =
                        excluded.stock_certificate_type_name,

                    par_value =
                        excluded.par_value,

                    sector_code =
                        excluded.sector_code,

                    sector_name =
                        excluded.sector_name,

                    industry_code =
                        excluded.industry_code,

                    industry_name =
                        excluded.industry_name,

                    shares_outstanding =
                        excluded.shares_outstanding,

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
                "security_id": security_id,
                "data_date": record.data_date,
                "market_code": record.market_code,
                "listing_status": record.listing_status,
                "source_market_name": record.source_market_name,
                "security_group_name": record.security_group_name,
                "section_type_name": record.section_type_name,
                "stock_certificate_type_name": (record.stock_certificate_type_name),
                "par_value": record.par_value,
                "sector_code": record.sector_code,
                "sector_name": record.sector_name,
                "industry_code": record.industry_code,
                "industry_name": record.industry_name,
                "shares_outstanding": record.shares_outstanding,
                "market_cap": record.market_cap,
                "available_at": record.available_at,
                "collected_at": collected_at,
                "source_id": source_id,
                "collection_run_id": collection_run_id,
            },
        )

    def count_history_rows(
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
                from public.security_master_history
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
        records: list[SecurityMasterRecord],
        source_id: UUID,
        collection_run_id: UUID | None,
    ) -> int:
        saved_count = 0

        for record in records:
            security_id = self.upsert_security(record)

            self.upsert_history(
                security_id=security_id,
                record=record,
                source_id=source_id,
                collection_run_id=collection_run_id,
            )

            saved_count += 1

        return saved_count
