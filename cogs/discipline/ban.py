import discord


async def issue_ban(
    member: discord.Member
):
    try:
        await member.ban(
            reason="Disciplinary ban"
        )

    except discord.Forbidden:
        return (
            False,
            "I don't have permission to ban that member."
        )

    except discord.HTTPException:
        return (
            False,
            "Discord rejected the ban."
        )

    return (
        True,
        f"{member.mention} has been permanently banned."
    )
