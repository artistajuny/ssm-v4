-- ============================================================
-- SSM V4
-- Initial Database Schema
-- ============================================================


-- ============================================================
-- Extensions
-- ============================================================

create extension if not exists pgcrypto;


-- ============================================================
-- Common updated_at trigger
-- ============================================================

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


-- ============================================================
-- 1. Data Source / Collection Management
-- ============================================================

create table public.data_sources (
    id uuid primary key default gen_random_uuid(),

    source_code text not null unique,
    source_name text not null,

    source_type text not null,

    base_url text,

    timezone text not null default 'Asia/Seoul',

    expected_delay_minutes integer,

    is_active boolean not null default true,

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


create table public.market_calendar (
    calendar_date date primary key,

    market_code text not null default 'KR',

    is_trading_day boolean not null,

    open_at timestamptz,
    close_at timestamptz,

    holiday_name text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


create table public.collection_runs (
    id uuid primary key default gen_random_uuid(),

    source_id uuid not null
        references public.data_sources(id),

    collector_name text not null,

    dataset_name text not null,

    start_date date,
    end_date date,

    run_type text not null
        check (
            run_type in (
                'BACKFILL',
                'INCREMENTAL',
                'RETRY',
                'MANUAL'
            )
        ),

    status text not null
        check (
            status in (
                'PENDING',
                'RUNNING',
                'SUCCESS',
                'PARTIAL_SUCCESS',
                'FAILED'
            )
        ),

    started_at timestamptz,
    finished_at timestamptz,

    rows_received bigint not null default 0,
    rows_inserted bigint not null default 0,
    rows_updated bigint not null default 0,
    rows_rejected bigint not null default 0,

    error_message text,

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now()
);


create table public.ingestion_watermarks (
    id uuid primary key default gen_random_uuid(),

    source_id uuid not null
        references public.data_sources(id),

    dataset_name text not null,

    last_success_data_date date,
    last_success_available_at timestamptz,
    last_success_collected_at timestamptz,

    updated_at timestamptz not null default now(),

    unique (
        source_id,
        dataset_name
    )
);


create table public.data_quality_issues (
    id uuid primary key default gen_random_uuid(),

    source_id uuid
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    dataset_name text not null,

    data_date date,

    severity text not null
        check (
            severity in (
                'INFO',
                'WARNING',
                'ERROR',
                'CRITICAL'
            )
        ),

    issue_code text not null,
    issue_message text not null,

    details jsonb not null default '{}'::jsonb,

    resolved boolean not null default false,
    resolved_at timestamptz,

    created_at timestamptz not null default now()
);


-- ============================================================
-- 2. Model / Feature Version Management
-- ============================================================

create table public.feature_versions (
    id uuid primary key default gen_random_uuid(),

    feature_scope text not null,
    version_code text not null,

    description text,

    config jsonb not null default '{}'::jsonb,

    is_active boolean not null default false,

    created_at timestamptz not null default now(),

    unique (
        feature_scope,
        version_code
    )
);


create table public.model_versions (
    id uuid primary key default gen_random_uuid(),

    model_scope text not null,

    version_code text not null,

    description text,

    parameters jsonb not null default '{}'::jsonb,

    is_active boolean not null default false,

    created_at timestamptz not null default now(),

    unique (
        model_scope,
        version_code
    )
);


create table public.model_runs (
    id uuid primary key default gen_random_uuid(),

    model_version_id uuid not null
        references public.model_versions(id),

    data_date date,

    started_at timestamptz not null default now(),
    finished_at timestamptz,

    status text not null
        check (
            status in (
                'PENDING',
                'RUNNING',
                'SUCCESS',
                'FAILED'
            )
        ),

    rows_processed bigint not null default 0,

    error_message text,

    metadata jsonb not null default '{}'::jsonb
);


-- ============================================================
-- 3. Security Master
-- ============================================================

create table public.security_master (
    id uuid primary key default gen_random_uuid(),

    ticker text not null,

    isin text,

    name_ko text not null,
    name_en text,

    security_type text not null default 'STOCK',

    first_listed_date date,
    final_delisted_date date,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (ticker)
);


create unique index uq_security_master_isin
on public.security_master(isin)
where isin is not null;


create table public.security_master_history (
    id uuid primary key default gen_random_uuid(),

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    market_code text not null,

    listing_status text not null
        check (
            listing_status in (
                'LISTED',
                'SUSPENDED',
                'DELISTED'
            )
        ),

    sector_code text,
    sector_name text,

    industry_code text,
    industry_name text,

    shares_outstanding bigint,
    market_cap bigint,

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    created_at timestamptz not null default now(),

    unique (
        security_id,
        data_date,
        source_id
    )
);


-- ============================================================
-- 4. Market Index RAW
-- ============================================================

create table public.raw_market_index_daily (
    id bigint generated always as identity primary key,

    index_code text not null,

    data_date date not null,

    open numeric(20,6),
    high numeric(20,6),
    low numeric(20,6),
    close numeric(20,6),

    volume bigint,
    trading_value numeric(24,2),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        index_code,
        data_date,
        source_id
    )
);


-- ============================================================
-- 5. Stock Daily RAW
-- ============================================================

create table public.raw_stock_daily (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    open numeric(20,4),
    high numeric(20,4),
    low numeric(20,4),
    close numeric(20,4),

    adjusted_close numeric(20,4),

    volume bigint,
    trading_value numeric(24,2),

    market_cap numeric(24,2),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        security_id,
        data_date,
        source_id
    )
);


-- ============================================================
-- 6. Market Investor Flow RAW
-- ============================================================

create table public.raw_market_investor_flow_daily (
    id bigint generated always as identity primary key,

    market_code text not null,

    data_date date not null,

    investor_type text not null,

    buy_value numeric(24,2),
    sell_value numeric(24,2),
    net_buy_value numeric(24,2),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        market_code,
        data_date,
        investor_type,
        source_id
    )
);


-- ============================================================
-- 7. Stock Investor Flow RAW
-- ============================================================

create table public.raw_stock_investor_flow_daily (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    investor_type text not null,

    buy_value numeric(24,2),
    sell_value numeric(24,2),
    net_buy_value numeric(24,2),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        security_id,
        data_date,
        investor_type,
        source_id
    )
);


-- ============================================================
-- 8. Credit / Deposit / Forced Liquidation RAW
-- ============================================================

create table public.raw_credit_daily (
    id bigint generated always as identity primary key,

    data_date date not null,

    market_code text not null default 'KR',

    credit_balance numeric(24,2),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        data_date,
        market_code,
        source_id
    )
);


create table public.raw_deposit_daily (
    id bigint generated always as identity primary key,

    data_date date not null,

    investor_deposit numeric(24,2),
    cma_balance numeric(24,2),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        data_date,
        source_id
    )
);


create table public.raw_forced_liquidation_daily (
    id bigint generated always as identity primary key,

    data_date date not null,

    liquidation_value numeric(24,2),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        data_date,
        source_id
    )
);


-- ============================================================
-- 9. Short Selling RAW
-- ============================================================

create table public.raw_short_market_daily (
    id bigint generated always as identity primary key,

    market_code text not null,

    data_date date not null,

    short_volume bigint,
    short_value numeric(24,2),
    short_ratio numeric(12,6),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        market_code,
        data_date,
        source_id
    )
);


create table public.raw_short_stock_daily (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    short_volume bigint,
    short_value numeric(24,2),
    short_ratio numeric(12,6),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        security_id,
        data_date,
        source_id
    )
);


create table public.raw_short_balance_stock_daily (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    short_balance_quantity bigint,
    short_balance_value numeric(24,2),
    short_balance_ratio numeric(12,6),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        security_id,
        data_date,
        source_id
    )
);


-- ============================================================
-- 10. Lending RAW
-- ============================================================

create table public.raw_lending_market_daily (
    id bigint generated always as identity primary key,

    market_code text not null,

    data_date date not null,

    lending_balance_quantity bigint,
    lending_balance_value numeric(24,2),

    lending_new_quantity bigint,
    lending_return_quantity bigint,

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        market_code,
        data_date,
        source_id
    )
);


create table public.raw_lending_stock_daily (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    lending_balance_quantity bigint,
    lending_balance_value numeric(24,2),

    lending_new_quantity bigint,
    lending_return_quantity bigint,

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        security_id,
        data_date,
        source_id
    )
);


-- ============================================================
-- 11. Global Market / FX / Rates RAW
-- ============================================================

create table public.raw_global_market_daily (
    id bigint generated always as identity primary key,

    series_code text not null,

    data_date date not null,

    open numeric(20,6),
    high numeric(20,6),
    low numeric(20,6),
    close numeric(20,6),

    volume bigint,

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        series_code,
        data_date,
        source_id
    )
);


create table public.raw_fx_daily (
    id bigint generated always as identity primary key,

    pair_code text not null,

    data_date date not null,

    open numeric(20,8),
    high numeric(20,8),
    low numeric(20,8),
    close numeric(20,8),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        pair_code,
        data_date,
        source_id
    )
);


create table public.raw_rates_daily (
    id bigint generated always as identity primary key,

    series_code text not null,

    data_date date not null,

    rate_value numeric(12,6),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        series_code,
        data_date,
        source_id
    )
);


-- ============================================================
-- 12. Financial RAW
-- ============================================================

create table public.raw_financial_quarterly (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    period_end date not null,

    fiscal_year integer not null,
    fiscal_quarter integer not null
        check (fiscal_quarter between 1 and 4),

    statement_type text not null,

    revenue numeric(24,2),
    operating_income numeric(24,2),
    net_income numeric(24,2),
    operating_cash_flow numeric(24,2),

    total_assets numeric(24,2),
    total_liabilities numeric(24,2),
    total_equity numeric(24,2),

    available_at timestamptz not null,
    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        security_id,
        period_end,
        statement_type,
        source_id
    )
);


-- ============================================================
-- 13. Intraday Market RAW Snapshot
-- ============================================================

create table public.raw_market_intraday_snapshot (
    id bigint generated always as identity primary key,

    market_code text not null,

    snapshot_at timestamptz not null,

    index_value numeric(20,6),
    index_change_pct numeric(12,6),

    advancers integer,
    decliners integer,
    unchanged integer,

    sharp_decline_count integer,

    trading_value numeric(24,2),

    intraday_volatility numeric(12,6),

    collected_at timestamptz not null default now(),

    source_id uuid not null
        references public.data_sources(id),

    collection_run_id uuid
        references public.collection_runs(id),

    unique (
        market_code,
        snapshot_at,
        source_id
    )
);


-- ============================================================
-- 14. Market Features
-- ============================================================

create table public.market_features_daily (
    id bigint generated always as identity primary key,

    market_code text not null,
    data_date date not null,

    feature_version_id uuid not null
        references public.feature_versions(id),

    index_return_1d numeric(12,6),
    index_return_5d numeric(12,6),
    index_return_20d numeric(12,6),

    index_ma20_gap numeric(12,6),
    index_ma60_gap numeric(12,6),
    index_ma120_gap numeric(12,6),
    index_ma200_gap numeric(12,6),

    advancers integer,
    decliners integer,
    unchanged integer,

    advance_decline_ratio numeric(12,6),

    pct_above_ma20 numeric(12,6),
    pct_above_ma60 numeric(12,6),
    pct_above_ma120 numeric(12,6),
    pct_above_ma200 numeric(12,6),

    new_high_count integer,
    new_low_count integer,

    foreign_flow_1d_ratio numeric(12,6),
    foreign_flow_5d_ratio numeric(12,6),
    foreign_flow_20d_ratio numeric(12,6),

    institution_flow_1d_ratio numeric(12,6),
    institution_flow_5d_ratio numeric(12,6),
    institution_flow_20d_ratio numeric(12,6),

    credit_balance_change_5d numeric(12,6),
    credit_balance_zscore numeric(12,6),

    investor_deposit_change_5d numeric(12,6),
    investor_deposit_zscore numeric(12,6),

    credit_deposit_ratio numeric(12,6),

    forced_liquidation_5d_avg numeric(24,2),
    forced_liquidation_zscore numeric(12,6),

    realized_volatility_20d numeric(12,6),

    drawdown_20d numeric(12,6),
    drawdown_60d numeric(12,6),

    vix_value numeric(12,6),
    usdkrw_change_1d numeric(12,6),
    us_2y_change numeric(12,6),
    us_10y_change numeric(12,6),

    extra_features jsonb not null default '{}'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        market_code,
        data_date,
        feature_version_id
    )
);


-- ============================================================
-- 15. Stock Features
-- ============================================================

create table public.stock_features_daily (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    feature_version_id uuid not null
        references public.feature_versions(id),

    return_1d numeric(12,6),
    return_5d numeric(12,6),
    return_20d numeric(12,6),
    return_60d numeric(12,6),

    ma20_gap numeric(12,6),
    ma60_gap numeric(12,6),
    ma120_gap numeric(12,6),
    ma200_gap numeric(12,6),

    rsi_14 numeric(12,6),

    volatility_20d numeric(12,6),
    volatility_60d numeric(12,6),

    drawdown_20d numeric(12,6),
    drawdown_60d numeric(12,6),
    drawdown_120d numeric(12,6),

    avg_trading_value_20d numeric(24,2),

    relative_strength_20d numeric(12,6),
    relative_strength_60d numeric(12,6),

    foreign_flow_5d_ratio numeric(12,6),
    foreign_flow_20d_ratio numeric(12,6),

    institution_flow_5d_ratio numeric(12,6),
    institution_flow_20d_ratio numeric(12,6),

    short_ratio_5d numeric(12,6),
    short_ratio_20d numeric(12,6),

    short_balance_ratio numeric(12,6),

    lending_balance_ratio numeric(12,6),

    extra_features jsonb not null default '{}'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        security_id,
        data_date,
        feature_version_id
    )
);


-- ============================================================
-- 16. Fundamental Features
-- ============================================================

create table public.fundamental_features_quarterly (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    period_end date not null,

    feature_version_id uuid not null
        references public.feature_versions(id),

    roe numeric(12,6),
    debt_ratio numeric(12,6),
    operating_margin numeric(12,6),

    revenue_growth_yoy numeric(12,6),
    operating_income_growth_yoy numeric(12,6),
    net_income_growth_yoy numeric(12,6),

    operating_cash_flow_margin numeric(12,6),

    extra_features jsonb not null default '{}'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        security_id,
        period_end,
        feature_version_id
    )
);


-- ============================================================
-- 17. Market Risk
-- ============================================================

create table public.market_risk_results_daily (
    id bigint generated always as identity primary key,

    market_code text not null,
    data_date date not null,

    feature_version_id uuid not null
        references public.feature_versions(id),

    model_version_id uuid not null
        references public.model_versions(id),

    risk_score numeric(6,3) not null
        check (risk_score between 0 and 100),

    trend_risk numeric(6,3),
    breadth_risk numeric(6,3),
    flow_risk numeric(6,3),
    liquidity_risk numeric(6,3),
    leverage_risk numeric(6,3),
    stress_risk numeric(6,3),
    volatility_risk numeric(6,3),
    global_risk numeric(6,3),

    freshness_score numeric(6,3),
    confidence_score numeric(6,3),

    major_risks jsonb not null default '[]'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        market_code,
        data_date,
        model_version_id
    )
);


-- ============================================================
-- 18. Market Opportunity
-- ============================================================

create table public.market_opportunity_results_daily (
    id bigint generated always as identity primary key,

    market_code text not null,
    data_date date not null,

    feature_version_id uuid not null
        references public.feature_versions(id),

    model_version_id uuid not null
        references public.model_versions(id),

    opportunity_score numeric(6,3) not null
        check (opportunity_score between 0 and 100),

    trend_score numeric(6,3),
    breadth_score numeric(6,3),
    flow_score numeric(6,3),
    valuation_score numeric(6,3),
    volatility_score numeric(6,3),
    global_score numeric(6,3),

    freshness_score numeric(6,3),
    confidence_score numeric(6,3),

    positive_factors jsonb not null default '[]'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        market_code,
        data_date,
        model_version_id
    )
);


-- ============================================================
-- 19. Market Regime
-- ============================================================

create table public.market_regime_results_daily (
    id bigint generated always as identity primary key,

    market_code text not null,
    data_date date not null,

    model_version_id uuid not null
        references public.model_versions(id),

    market_risk_result_id bigint
        references public.market_risk_results_daily(id),

    market_opportunity_result_id bigint
        references public.market_opportunity_results_daily(id),

    regime text not null
        check (
            regime in (
                'RISK_ON',
                'NEUTRAL',
                'CAUTION',
                'RISK_OFF',
                'PANIC'
            )
        ),

    calculated_at timestamptz not null default now(),

    unique (
        market_code,
        data_date,
        model_version_id
    )
);


-- ============================================================
-- 20. Stock Risk
-- ============================================================

create table public.stock_risk_results_daily (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    feature_version_id uuid not null
        references public.feature_versions(id),

    model_version_id uuid not null
        references public.model_versions(id),

    risk_score numeric(6,3) not null
        check (risk_score between 0 and 100),

    trend_risk numeric(6,3),
    momentum_risk numeric(6,3),
    volatility_risk numeric(6,3),
    drawdown_risk numeric(6,3),
    liquidity_risk numeric(6,3),
    relative_strength_risk numeric(6,3),
    flow_risk numeric(6,3),
    short_risk numeric(6,3),
    fundamental_risk numeric(6,3),

    freshness_score numeric(6,3),
    confidence_score numeric(6,3),

    major_risks jsonb not null default '[]'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        security_id,
        data_date,
        model_version_id
    )
);


-- ============================================================
-- 21. Stock Opportunity
-- ============================================================

create table public.stock_opportunity_results_daily (
    id bigint generated always as identity primary key,

    security_id uuid not null
        references public.security_master(id),

    data_date date not null,

    feature_version_id uuid not null
        references public.feature_versions(id),

    model_version_id uuid not null
        references public.model_versions(id),

    opportunity_score numeric(6,3) not null
        check (opportunity_score between 0 and 100),

    trend_score numeric(6,3),
    momentum_score numeric(6,3),
    relative_strength_score numeric(6,3),
    flow_score numeric(6,3),
    valuation_score numeric(6,3),
    fundamental_score numeric(6,3),

    freshness_score numeric(6,3),
    confidence_score numeric(6,3),

    positive_factors jsonb not null default '[]'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        security_id,
        data_date,
        model_version_id
    )
);


-- ============================================================
-- 22. User Profile
-- ============================================================

create table public.profiles (
    user_id uuid primary key
        references auth.users(id)
        on delete cascade,

    display_name text,

    trial_started_at timestamptz not null default now(),
    trial_ends_at timestamptz not null default (now() + interval '30 days'),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ============================================================
-- 23. Subscription
-- ============================================================

create table public.subscriptions (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    provider text,

    provider_customer_id text,
    provider_subscription_id text,

    status text not null
        check (
            status in (
                'INACTIVE',
                'ACTIVE',
                'PAST_DUE',
                'CANCELED',
                'EXPIRED'
            )
        ),

    started_at timestamptz,
    current_period_start timestamptz,
    current_period_end timestamptz,
    canceled_at timestamptz,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


create unique index uq_subscription_provider_id
on public.subscriptions(provider, provider_subscription_id)
where provider_subscription_id is not null;


-- ============================================================
-- 24. Plan Limits
-- ============================================================

create table public.plan_limits (
    id uuid primary key default gen_random_uuid(),

    plan_code text not null
        check (
            plan_code in (
                'FREE',
                'TRIAL_PRO',
                'PRO'
            )
        ),

    feature_code text not null,

    daily_limit integer,

    resource_limit integer,

    is_enabled boolean not null default true,

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        plan_code,
        feature_code
    )
);


-- ============================================================
-- 25. Usage Events
-- ============================================================

create table public.usage_events (
    id bigint generated always as identity primary key,

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    feature_code text not null,

    plan_code text not null,

    usage_count integer not null default 1
        check (usage_count > 0),

    occurred_at timestamptz not null default now(),

    metadata jsonb not null default '{}'::jsonb
);


-- ============================================================
-- 26. Portfolio
-- ============================================================

create table public.portfolios (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    name text not null,

    base_currency text not null default 'KRW',

    cash_amount numeric(24,2) not null default 0,

    is_active boolean not null default true,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


create table public.portfolio_positions (
    id uuid primary key default gen_random_uuid(),

    portfolio_id uuid not null
        references public.portfolios(id)
        on delete cascade,

    security_id uuid not null
        references public.security_master(id),

    quantity numeric(24,8) not null
        check (quantity >= 0),

    average_price numeric(20,4) not null
        check (average_price >= 0),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        portfolio_id,
        security_id
    )
);


create table public.portfolio_snapshots (
    id uuid primary key default gen_random_uuid(),

    portfolio_id uuid not null
        references public.portfolios(id)
        on delete cascade,

    data_date date not null,

    total_value numeric(24,2) not null,
    invested_value numeric(24,2) not null,
    cash_value numeric(24,2) not null,

    cash_ratio numeric(12,6),

    created_at timestamptz not null default now(),

    unique (
        portfolio_id,
        data_date
    )
);


create table public.portfolio_position_snapshots (
    id bigint generated always as identity primary key,

    portfolio_snapshot_id uuid not null
        references public.portfolio_snapshots(id)
        on delete cascade,

    security_id uuid not null
        references public.security_master(id),

    quantity numeric(24,8) not null,

    price numeric(20,4) not null,

    market_value numeric(24,2) not null,

    weight numeric(12,6) not null,

    unique (
        portfolio_snapshot_id,
        security_id
    )
);


-- ============================================================
-- 27. Portfolio Risk
-- ============================================================

create table public.portfolio_risk_results_daily (
    id bigint generated always as identity primary key,

    portfolio_id uuid not null
        references public.portfolios(id)
        on delete cascade,

    data_date date not null,

    model_version_id uuid not null
        references public.model_versions(id),

    portfolio_risk_score numeric(6,3) not null
        check (portfolio_risk_score between 0 and 100),

    weighted_stock_risk numeric(6,3),
    market_risk numeric(6,3),

    cash_ratio numeric(12,6),

    stock_concentration numeric(12,6),
    sector_concentration numeric(12,6),

    hhi numeric(12,6),

    cash_buffer_score numeric(6,3),

    freshness_score numeric(6,3),
    confidence_score numeric(6,3),

    risk_factors jsonb not null default '[]'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        portfolio_id,
        data_date,
        model_version_id
    )
);


-- ============================================================
-- 28. Decision Engine
-- ============================================================

create table public.decision_results_daily (
    id bigint generated always as identity primary key,

    data_date date not null,

    decision_scope text not null
        check (
            decision_scope in (
                'MARKET',
                'STOCK',
                'PORTFOLIO',
                'PORTFOLIO_STOCK'
            )
        ),

    security_id uuid
        references public.security_master(id),

    portfolio_id uuid
        references public.portfolios(id)
        on delete cascade,

    model_version_id uuid not null
        references public.model_versions(id),

    market_risk numeric(6,3),
    market_opportunity numeric(6,3),

    stock_risk numeric(6,3),
    stock_opportunity numeric(6,3),

    portfolio_risk numeric(6,3),

    cash_ratio numeric(12,6),
    position_weight numeric(12,6),

    confidence_score numeric(6,3),
    freshness_score numeric(6,3),

    decision_code text not null
        check (
            decision_code in (
                'AGGRESSIVE',
                'NORMAL',
                'CAUTIOUS',
                'SMALL_ENTRY',
                'HOLD',
                'DEFENSIVE',
                'NO_NEW_POSITION'
            )
        ),

    reasons jsonb not null default '[]'::jsonb,

    calculated_at timestamptz not null default now()
);


create unique index uq_decision_results_daily
on public.decision_results_daily (
    data_date,
    decision_scope,
    coalesce(
        security_id,
        '00000000-0000-0000-0000-000000000000'::uuid
    ),
    coalesce(
        portfolio_id,
        '00000000-0000-0000-0000-000000000000'::uuid
    ),
    model_version_id
);


-- ============================================================
-- 29. Intraday Market Risk
-- ============================================================

create table public.market_intraday_risk_results (
    id bigint generated always as identity primary key,

    market_code text not null,

    snapshot_at timestamptz not null,

    model_version_id uuid not null
        references public.model_versions(id),

    risk_score numeric(6,3) not null
        check (risk_score between 0 and 100),

    confidence_score numeric(6,3),

    factors jsonb not null default '{}'::jsonb,

    calculated_at timestamptz not null default now(),

    unique (
        market_code,
        snapshot_at,
        model_version_id
    )
);


-- ============================================================
-- 30. Backtest
-- ============================================================

create table public.backtest_runs (
    id uuid primary key default gen_random_uuid(),

    backtest_type text not null
        check (
            backtest_type in (
                'MARKET',
                'STOCK',
                'DECISION'
            )
        ),

    name text not null,

    start_date date not null,
    end_date date not null,

    config jsonb not null default '{}'::jsonb,

    status text not null
        check (
            status in (
                'PENDING',
                'RUNNING',
                'SUCCESS',
                'FAILED'
            )
        ),

    started_at timestamptz,
    finished_at timestamptz,

    error_message text,

    created_at timestamptz not null default now()
);


create table public.backtest_metrics (
    id bigint generated always as identity primary key,

    backtest_run_id uuid not null
        references public.backtest_runs(id)
        on delete cascade,

    metric_name text not null,

    metric_value numeric(24,8),

    metadata jsonb not null default '{}'::jsonb,

    unique (
        backtest_run_id,
        metric_name
    )
);


create table public.backtest_bucket_results (
    id bigint generated always as identity primary key,

    backtest_run_id uuid not null
        references public.backtest_runs(id)
        on delete cascade,

    bucket_name text not null,

    horizon_days integer,

    observation_count bigint,

    average_return numeric(12,8),
    median_return numeric(12,8),

    average_mdd numeric(12,8),

    positive_return_ratio numeric(12,8),

    metadata jsonb not null default '{}'::jsonb
);


-- ============================================================
-- 31. AI Copilot Execution Metadata
-- ============================================================

create table public.ai_copilot_runs (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    request_type text not null,

    analysis_data_date date,

    market_risk numeric(6,3),
    market_opportunity numeric(6,3),
    stock_risk numeric(6,3),
    stock_opportunity numeric(6,3),
    portfolio_risk numeric(6,3),

    decision_code text,

    freshness_score numeric(6,3),
    confidence_score numeric(6,3),

    model_name text,

    input_tokens integer,
    output_tokens integer,

    context_snapshot jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now()
);


-- ============================================================
-- 32. Operational Job Runs
-- ============================================================

create table public.job_runs (
    id uuid primary key default gen_random_uuid(),

    job_name text not null,

    job_type text not null,

    scheduled_for timestamptz,

    started_at timestamptz,
    finished_at timestamptz,

    status text not null
        check (
            status in (
                'PENDING',
                'RUNNING',
                'SUCCESS',
                'FAILED',
                'SKIPPED'
            )
        ),

    error_message text,

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now()
);


-- ============================================================
-- 33. Indexes
-- ============================================================

create index idx_security_master_history_date
on public.security_master_history(data_date);


create index idx_raw_stock_daily_security_date
on public.raw_stock_daily(security_id, data_date);


create index idx_raw_stock_daily_date
on public.raw_stock_daily(data_date);


create index idx_raw_market_index_daily_date
on public.raw_market_index_daily(data_date);


create index idx_stock_features_security_date
on public.stock_features_daily(security_id, data_date);


create index idx_market_features_market_date
on public.market_features_daily(market_code, data_date);


create index idx_stock_risk_security_date
on public.stock_risk_results_daily(security_id, data_date);


create index idx_stock_opportunity_security_date
on public.stock_opportunity_results_daily(security_id, data_date);


create index idx_usage_events_user_feature_time
on public.usage_events(
    user_id,
    feature_code,
    occurred_at
);


create index idx_collection_runs_dataset_status
on public.collection_runs(
    dataset_name,
    status,
    started_at
);


create index idx_data_quality_issues_unresolved
on public.data_quality_issues(
    resolved,
    severity,
    created_at
);


create index idx_job_runs_name_time
on public.job_runs(
    job_name,
    started_at
);


-- ============================================================
-- 34. updated_at triggers
-- ============================================================

create trigger trg_data_sources_updated_at
before update on public.data_sources
for each row
execute function public.set_updated_at();


create trigger trg_market_calendar_updated_at
before update on public.market_calendar
for each row
execute function public.set_updated_at();


create trigger trg_security_master_updated_at
before update on public.security_master
for each row
execute function public.set_updated_at();


create trigger trg_profiles_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();


create trigger trg_subscriptions_updated_at
before update on public.subscriptions
for each row
execute function public.set_updated_at();


create trigger trg_plan_limits_updated_at
before update on public.plan_limits
for each row
execute function public.set_updated_at();


create trigger trg_portfolios_updated_at
before update on public.portfolios
for each row
execute function public.set_updated_at();


create trigger trg_portfolio_positions_updated_at
before update on public.portfolio_positions
for each row
execute function public.set_updated_at();


-- ============================================================
-- 35. Auto-create Profile after signup
-- ============================================================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin

    insert into public.profiles (
        user_id,
        display_name
    )
    values (
        new.id,
        coalesce(
            new.raw_user_meta_data ->> 'display_name',
            ''
        )
    );

    return new;

end;
$$;


create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_user();