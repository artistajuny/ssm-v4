# SSM V4

SSM V4 is a quantitative stock-market risk, opportunity,
portfolio-risk and decision-support system focused primarily
on the Korean stock market.

## Core Principles

- Quantitative models make core investment assessments.
- AI does not calculate investment risk scores.
- AI explains results produced by quantitative engines.
- Raw data and calculated data are stored separately.
- Point-in-time availability is preserved.
- Look-ahead bias must be prevented.
- Survivorship bias must be prevented.
- Model results are versioned.
- Data collectors support both backfill and incremental updates.
- Data ingestion is idempotent and UPSERT based.
- Validation occurs before model calculations.

## Architecture

Data Sources

-> Collector

-> Validation

-> RAW Database

-> Feature Engine

-> Market Engine

-> Stock Engine

-> Fundamental Engine

-> Portfolio Engine

-> Opportunity Engine

-> Freshness / Confidence Engine

-> Decision Engine

-> Backtest Engine

-> FastAPI

-> AI Copilot

-> React Native App

## Technology

Backend:

- Python
- FastAPI

Database / Auth:

- Supabase PostgreSQL
- Supabase Auth

Data Processing:

- Pandas
- NumPy
- SciPy

Mobile:

- React Native
- Expo

Worker:

- Python Worker
- Scheduler

## Environments

SSM V4 is designed for:

- DEVELOPMENT
- STAGING
- PRODUCTION