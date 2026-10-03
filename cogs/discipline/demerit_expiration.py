from datetime import datetime, timezone


def is_demerit_active(expires_at: str | None) -> bool:
    if expires_at is None:
        return True

    expiration_datetime = datetime.fromisoformat(
        expires_at
    )

    if expiration_datetime.tzinfo is None:
        expiration_datetime = expiration_datetime.replace(
            tzinfo=timezone.utc
        )

    return datetime.now(timezone.utc) < expiration_datetime
