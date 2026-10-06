-- ============================================================
-- SSM V4
-- STEP 4
-- Enhance Market Index / Stock Daily RAW
-- ============================================================


-- ============================================================
-- 1. Market Index RAW
-- ============================================================

alter table public.raw_market_index_daily
alter column index_code drop not null;


alter table public.raw_market_index_daily
add column if not exists source_index_class text;

alter table public.raw_market_index_daily
add column if not exists source_index_name text;

alter table public.raw_market_index_daily
add column if not exists change_value numeric(20, 6);

alter table public.raw_market_index_daily
add column if not exists change_rate numeric(12, 6);

alter table public.raw_market_index_daily
add column if not exists market_cap numeric(24, 2);


alter table public.raw_market_index_daily
drop constraint if exists raw_market_index_daily_index_code_data_date_source_id_key;


create unique index if not exists uq_raw_market_index_source_identity
on public.raw_market_index_daily (
    source_index_class,
    source_index_name,
    data_date,
    source_id
);


create index if not exists idx_raw_market_index_code_date
on public.raw_market_index_daily (
    index_code,
    data_date
)
where index_code is not null;


-- ============================================================
-- 2. Stock Daily RAW
-- ============================================================

alter table public.raw_stock_daily
drop column if exists adjusted_close;


alter table public.raw_stock_daily
add column if not exists source_ticker text;

alter table public.raw_stock_daily
add column if not exists source_stock_name text;

alter table public.raw_stock_daily
add column if not exists source_market_name text;

alter table public.raw_stock_daily
add column if not exists source_section_name text;

alter table public.raw_stock_daily
add column if not exists change_value numeric(20, 4);

alter table public.raw_stock_daily
add column if not exists change_rate numeric(12, 6);

alter table public.raw_stock_daily
add column if not exists shares_outstanding bigint;


create index if not exists idx_raw_stock_daily_source_ticker_date
on public.raw_stock_daily (
    source_ticker,
    data_date
);