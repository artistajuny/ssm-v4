from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def clean_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def parse_krx_date(
    value: Any,
) -> date | None:
    text = clean_text(value)

    if text is None:
        return None

    formats = (
        "%Y%m%d",
        "%Y-%m-%d",
        "%Y/%m/%d",
    )

    for date_format in formats:
        try:
            return datetime.strptime(
                text,
                date_format,
            ).date()
        except ValueError:
            continue

    raise ValueError(f"Unsupported KRX date value: {text}")


def parse_decimal(
    value: Any,
) -> Decimal | None:
    text = clean_text(value)

    if text is None:
        return None

    if text in {
        "-",
        "N/A",
        "해당없음",
        "무액면",
    }:
        return None

    normalized = text.replace(",", "")

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid KRX decimal value: {text}") from exc


def parse_int(
    value: Any,
) -> int | None:
    decimal_value = parse_decimal(value)

    if decimal_value is None:
        return None

    return int(decimal_value)
