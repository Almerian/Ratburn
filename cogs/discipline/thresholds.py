def get_punishment_tier(
    active_demerit_count: int,
    config
) -> str:
    ban_threshold = (
        config["ban_demerit_threshold"]
        if config is not None
        else None
    )

    detention_threshold = (
        config["detention_demerit_threshold"]
        if config is not None
        else None
    )

    mute_threshold = (
        config["mute_demerit_threshold"]
        if config is not None
        else None
    )

    if (
        ban_threshold is not None
        and active_demerit_count >= ban_threshold
    ):
        return "ban"

    if (
        detention_threshold is not None
        and active_demerit_count >= detention_threshold
    ):
        return "detention"

    if (
        mute_threshold is not None
        and active_demerit_count >= mute_threshold
    ):
        return "mute"

    if active_demerit_count >= 1:
        return "demerit"

    return "warning"
