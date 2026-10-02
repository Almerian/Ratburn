from datetime import datetime, timezone, timedelta


def get_expiration_delta(
    value: int | None,
    unit: str | None
) -> timedelta | None:
    if value is None or unit is None:
        return None

    if unit == "days":
        return timedelta(days=value)

    if unit == "weeks":
        return timedelta(weeks=value)

    if unit == "months":
        return timedelta(days=value * 30)

    if unit == "never":
        return None

    return None


def is_demerit_active(
    created_at: str,
    expiration_value: int | None,
    expiration_unit: str | None
) -> bool:
    expiration_delta = get_expiration_delta(
        expiration_value,
        expiration_unit
    )

    if expiration_delta is None:
        return True

    created_datetime = datetime.fromisoformat(
        created_at
    )

    if created_datetime.tzinfo is None:
        created_datetime = created_datetime.replace(
            tzinfo=timezone.utc
        )

    expiration_time = (
        created_datetime + expiration_delta
    )

    return datetime.now(
        timezone.utc
    ) < expiration_time
