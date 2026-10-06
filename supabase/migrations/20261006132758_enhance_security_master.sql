-- ============================================================
-- SSM V4
-- Enhance Security Master
-- ============================================================


-- ============================================================
-- 1. Security master additional source fields
-- ============================================================

alter table public.security_master
add column if not exists name_abbr_ko text;


-- ============================================================
-- 2. Preserve KRX classification fields by data date
-- ============================================================

alter table public.security_master_history
add column if not exists source_market_name text;

alter table public.security_master_history
add column if not exists security_group_name text;

alter table public.security_master_history
add column if not exists section_type_name text;

alter table public.security_master_history
add column if not exists stock_certificate_type_name text;

alter table public.security_master_history
add column if not exists par_value numeric(20, 4);


-- ============================================================
-- 3. Ticker must not be treated as permanent historical ID
-- ============================================================

alter table public.security_master
drop constraint if exists security_master_ticker_key;


create index if not exists idx_security_master_ticker
on public.security_master(ticker);