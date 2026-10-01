from datetime import datetime, timedelta, timezone

import discord


CLEANUP_WINDOW = timedelta(minutes=15)


async def cleanup_recent_messages(
    guild: discord.Guild,
    user: discord.Member
) -> dict:
    """
    Delete messages from a banned user that are less than
    15 minutes old.

    Returns a summary of the cleanup attempt.
    """

    cutoff = datetime.now(timezone.utc) - CLEANUP_WINDOW

    found = 0
    deleted = 0
    failed = 0

    for channel in guild.text_channels:
        try:
            async for message in channel.history(
                after=cutoff,
                oldest_first=False
            ):
                if message.author.id != user.id:
                    continue

                found += 1

                try:
                    await message.delete()
                    deleted += 1
                except discord.HTTPException:
                    failed += 1

        except (discord.Forbidden, discord.HTTPException):
            continue

    return {
        "found": found,
        "deleted": deleted,
        "failed": failed,
    }
