from collections import Counter

from data_pipeline.collectors.master.models import SecurityMasterRecord

VALID_MARKET_CODES = {
    "KOSPI",
    "KOSDAQ",
    "KONEX",
}

VALID_LISTING_STATUSES = {
    "LISTED",
    "SUSPENDED",
    "DELISTED",
}


class MasterValidationError(ValueError):
    pass


def validate_security_master_records(
    records: list[SecurityMasterRecord],
) -> None:
    if not records:
        raise MasterValidationError("Security master collection returned zero records.")

    ticker_date_keys = [
        (
            record.ticker,
            record.data_date,
        )
        for record in records
    ]

    duplicate_ticker_date_keys = [
        key for key, count in Counter(ticker_date_keys).items() if count > 1
    ]

    if duplicate_ticker_date_keys:
        duplicate_text = ", ".join(
            f"{ticker}:{data_date}" for ticker, data_date in sorted(duplicate_ticker_date_keys)[:20]
        )

        raise MasterValidationError("Duplicate ticker/data_date pairs detected: " + duplicate_text)

    isin_date_keys = [
        (
            record.isin,
            record.data_date,
        )
        for record in records
        if record.isin
    ]

    duplicate_isin_date_keys = [key for key, count in Counter(isin_date_keys).items() if count > 1]

    if duplicate_isin_date_keys:
        duplicate_text = ", ".join(
            f"{isin}:{data_date}" for isin, data_date in sorted(duplicate_isin_date_keys)[:20]
        )

        raise MasterValidationError("Duplicate ISIN/data_date pairs detected: " + duplicate_text)

    for record in records:
        if not record.ticker:
            raise MasterValidationError("Ticker must not be empty.")

        if not record.isin:
            raise MasterValidationError(f"ISIN must not be empty ticker={record.ticker}")

        if not record.name_ko:
            raise MasterValidationError(f"Missing Korean name for ticker={record.ticker}")

        if record.market_code not in VALID_MARKET_CODES:
            raise MasterValidationError(
                f"Invalid market_code ticker={record.ticker}, market_code={record.market_code}"
            )

        if record.listing_status not in VALID_LISTING_STATUSES:
            raise MasterValidationError(
                "Invalid listing_status "
                f"ticker={record.ticker}, "
                f"listing_status={record.listing_status}"
            )

        if record.shares_outstanding is not None and record.shares_outstanding < 0:
            raise MasterValidationError(f"shares_outstanding must be >= 0 ticker={record.ticker}")

        if record.market_cap is not None and record.market_cap < 0:
            raise MasterValidationError(f"market_cap must be >= 0 ticker={record.ticker}")

        if record.par_value is not None and record.par_value < 0:
            raise MasterValidationError(f"par_value must be >= 0 ticker={record.ticker}")

        if (
            record.first_listed_date is not None
            and record.final_delisted_date is not None
            and record.final_delisted_date < record.first_listed_date
        ):
            raise MasterValidationError(
                f"final_delisted_date is before first_listed_date ticker={record.ticker}"
            )
