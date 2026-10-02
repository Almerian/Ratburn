import discord
from datetime import timedelta


async def issue_mute(
    member: discord.Member,
    duration_value: int | None,
    duration_unit: str | None
):
    if duration_value is None or duration_unit is None:
        return False, "Mute duration has not been configured."

    if duration_unit == "minutes":
        duration = timedelta(
            minutes=duration_value
        )

    elif duration_unit == "hours":
        duration = timedelta(
            hours=duration_value
        )

    elif duration_unit == "days":
        duration = timedelta(
            days=duration_value
        )

    else:
        return False, "The configured mute duration is invalid."

    try:
        await member.timeout(
            duration,
            reason="Disciplinary mute"
        )

    except discord.Forbidden:
        return (
            False,
            "I don't have permission to mute that member."
        )

    except discord.HTTPException:
        return (
            False,
            "Discord rejected the mute."
        )

    return (
        True,
        f"{member.mention} has been muted for "
        f"{duration_value} {duration_unit}."
    )
