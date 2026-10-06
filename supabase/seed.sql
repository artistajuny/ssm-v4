-- ============================================================
-- SSM V4
-- Development Seed Data
-- ============================================================


-- ============================================================
-- Initial Plan Limits
-- ============================================================

insert into public.plan_limits (
    plan_code,
    feature_code,
    daily_limit,
    resource_limit
)
values

    (
        'FREE',
        'MARKET_BASIC',
        null,
        null
    ),

    (
        'FREE',
        'MARKET_DETAIL',
        1,
        null
    ),

    (
        'FREE',
        'STOCK_ANALYSIS',
        5,
        null
    ),

    (
        'FREE',
        'STOCK_DEEP_ANALYSIS',
        2,
        null
    ),

    (
        'FREE',
        'PORTFOLIO_CREATE',
        null,
        1
    ),

    (
        'FREE',
        'PORTFOLIO_REANALYSIS',
        1,
        null
    ),

    (
        'FREE',
        'AI_COPILOT',
        3,
        null
    ),

    (
        'TRIAL_PRO',
        'MARKET_BASIC',
        null,
        null
    ),

    (
        'TRIAL_PRO',
        'MARKET_DETAIL',
        100,
        null
    ),

    (
        'TRIAL_PRO',
        'STOCK_ANALYSIS',
        100,
        null
    ),

    (
        'TRIAL_PRO',
        'STOCK_DEEP_ANALYSIS',
        50,
        null
    ),

    (
        'TRIAL_PRO',
        'PORTFOLIO_CREATE',
        null,
        20
    ),

    (
        'TRIAL_PRO',
        'PORTFOLIO_REANALYSIS',
        50,
        null
    ),

    (
        'TRIAL_PRO',
        'AI_COPILOT',
        50,
        null
    ),

    (
        'PRO',
        'MARKET_BASIC',
        null,
        null
    ),

    (
        'PRO',
        'MARKET_DETAIL',
        500,
        null
    ),

    (
        'PRO',
        'STOCK_ANALYSIS',
        500,
        null
    ),

    (
        'PRO',
        'STOCK_DEEP_ANALYSIS',
        200,
        null
    ),

    (
        'PRO',
        'PORTFOLIO_CREATE',
        null,
        100
    ),

    (
        'PRO',
        'PORTFOLIO_REANALYSIS',
        200,
        null
    ),

    (
        'PRO',
        'AI_COPILOT',
        200,
        null
    )

on conflict (
    plan_code,
    feature_code
)
do update
set
    daily_limit = excluded.daily_limit,
    resource_limit = excluded.resource_limit,
    updated_at = now();