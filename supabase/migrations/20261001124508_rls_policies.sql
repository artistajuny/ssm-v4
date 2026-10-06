-- ============================================================
-- SSM V4
-- Row Level Security Policies
-- ============================================================


-- ============================================================
-- Profiles
-- ============================================================

alter table public.profiles enable row level security;


create policy "Users can read own profile"
on public.profiles
for select
to authenticated
using (
    auth.uid() = user_id
);


create policy "Users can update own profile"
on public.profiles
for update
to authenticated
using (
    auth.uid() = user_id
)
with check (
    auth.uid() = user_id
);


-- ============================================================
-- Subscriptions
-- ============================================================

alter table public.subscriptions enable row level security;


create policy "Users can read own subscriptions"
on public.subscriptions
for select
to authenticated
using (
    auth.uid() = user_id
);


-- ============================================================
-- Plan Limits
-- ============================================================

alter table public.plan_limits enable row level security;


create policy "Authenticated users can read plan limits"
on public.plan_limits
for select
to authenticated
using (true);


-- ============================================================
-- Usage Events
-- ============================================================

alter table public.usage_events enable row level security;


create policy "Users can read own usage events"
on public.usage_events
for select
to authenticated
using (
    auth.uid() = user_id
);


-- ============================================================
-- Portfolios
-- ============================================================

alter table public.portfolios enable row level security;


create policy "Users can read own portfolios"
on public.portfolios
for select
to authenticated
using (
    auth.uid() = user_id
);


create policy "Users can insert own portfolios"
on public.portfolios
for insert
to authenticated
with check (
    auth.uid() = user_id
);


create policy "Users can update own portfolios"
on public.portfolios
for update
to authenticated
using (
    auth.uid() = user_id
)
with check (
    auth.uid() = user_id
);


create policy "Users can delete own portfolios"
on public.portfolios
for delete
to authenticated
using (
    auth.uid() = user_id
);


-- ============================================================
-- Portfolio Positions
-- ============================================================

alter table public.portfolio_positions enable row level security;


create policy "Users can read own portfolio positions"
on public.portfolio_positions
for select
to authenticated
using (
    exists (
        select 1
        from public.portfolios p
        where p.id = portfolio_positions.portfolio_id
          and p.user_id = auth.uid()
    )
);


create policy "Users can insert own portfolio positions"
on public.portfolio_positions
for insert
to authenticated
with check (
    exists (
        select 1
        from public.portfolios p
        where p.id = portfolio_positions.portfolio_id
          and p.user_id = auth.uid()
    )
);


create policy "Users can update own portfolio positions"
on public.portfolio_positions
for update
to authenticated
using (
    exists (
        select 1
        from public.portfolios p
        where p.id = portfolio_positions.portfolio_id
          and p.user_id = auth.uid()
    )
)
with check (
    exists (
        select 1
        from public.portfolios p
        where p.id = portfolio_positions.portfolio_id
          and p.user_id = auth.uid()
    )
);


create policy "Users can delete own portfolio positions"
on public.portfolio_positions
for delete
to authenticated
using (
    exists (
        select 1
        from public.portfolios p
        where p.id = portfolio_positions.portfolio_id
          and p.user_id = auth.uid()
    )
);


-- ============================================================
-- Portfolio Snapshots
-- ============================================================

alter table public.portfolio_snapshots enable row level security;


create policy "Users can read own portfolio snapshots"
on public.portfolio_snapshots
for select
to authenticated
using (
    exists (
        select 1
        from public.portfolios p
        where p.id = portfolio_snapshots.portfolio_id
          and p.user_id = auth.uid()
    )
);


-- ============================================================
-- Portfolio Position Snapshots
-- ============================================================

alter table public.portfolio_position_snapshots
enable row level security;


create policy "Users can read own position snapshots"
on public.portfolio_position_snapshots
for select
to authenticated
using (
    exists (
        select 1
        from public.portfolio_snapshots ps
        join public.portfolios p
          on p.id = ps.portfolio_id
        where ps.id =
              portfolio_position_snapshots.portfolio_snapshot_id
          and p.user_id = auth.uid()
    )
);


-- ============================================================
-- Portfolio Risk
-- ============================================================

alter table public.portfolio_risk_results_daily
enable row level security;


create policy "Users can read own portfolio risk"
on public.portfolio_risk_results_daily
for select
to authenticated
using (
    exists (
        select 1
        from public.portfolios p
        where p.id =
              portfolio_risk_results_daily.portfolio_id
          and p.user_id = auth.uid()
    )
);


-- ============================================================
-- Decision
-- ============================================================

alter table public.decision_results_daily
enable row level security;


create policy "Users can read own portfolio decisions"
on public.decision_results_daily
for select
to authenticated
using (
    portfolio_id is not null
    and exists (
        select 1
        from public.portfolios p
        where p.id =
              decision_results_daily.portfolio_id
          and p.user_id = auth.uid()
    )
);


-- ============================================================
-- AI Copilot
-- ============================================================

alter table public.ai_copilot_runs
enable row level security;


create policy "Users can read own AI runs"
on public.ai_copilot_runs
for select
to authenticated
using (
    auth.uid() = user_id
);


-- ============================================================
-- Internal tables
--
-- Enable RLS without user policies.
-- Backend service_role can still access these.
-- ============================================================

alter table public.data_sources enable row level security;
alter table public.market_calendar enable row level security;
alter table public.collection_runs enable row level security;
alter table public.ingestion_watermarks enable row level security;
alter table public.data_quality_issues enable row level security;

alter table public.feature_versions enable row level security;
alter table public.model_versions enable row level security;
alter table public.model_runs enable row level security;

alter table public.security_master enable row level security;
alter table public.security_master_history enable row level security;

alter table public.raw_market_index_daily enable row level security;
alter table public.raw_stock_daily enable row level security;

alter table public.raw_market_investor_flow_daily
enable row level security;

alter table public.raw_stock_investor_flow_daily
enable row level security;

alter table public.raw_credit_daily enable row level security;
alter table public.raw_deposit_daily enable row level security;

alter table public.raw_forced_liquidation_daily
enable row level security;

alter table public.raw_short_market_daily
enable row level security;

alter table public.raw_short_stock_daily
enable row level security;

alter table public.raw_short_balance_stock_daily
enable row level security;

alter table public.raw_lending_market_daily
enable row level security;

alter table public.raw_lending_stock_daily
enable row level security;

alter table public.raw_global_market_daily
enable row level security;

alter table public.raw_fx_daily enable row level security;
alter table public.raw_rates_daily enable row level security;

alter table public.raw_financial_quarterly
enable row level security;

alter table public.raw_market_intraday_snapshot
enable row level security;

alter table public.market_features_daily
enable row level security;

alter table public.stock_features_daily
enable row level security;

alter table public.fundamental_features_quarterly
enable row level security;

alter table public.market_risk_results_daily
enable row level security;

alter table public.market_opportunity_results_daily
enable row level security;

alter table public.market_regime_results_daily
enable row level security;

alter table public.stock_risk_results_daily
enable row level security;

alter table public.stock_opportunity_results_daily
enable row level security;

alter table public.market_intraday_risk_results
enable row level security;

alter table public.backtest_runs enable row level security;
alter table public.backtest_metrics enable row level security;
alter table public.backtest_bucket_results enable row level security;

alter table public.job_runs enable row level security;