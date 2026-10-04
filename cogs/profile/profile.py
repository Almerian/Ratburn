import calendar
import json

import discord
from discord import app_commands
from discord.ext import commands


def build_profile_embed(
    member: discord.Member,
    profile
):
    embed = discord.Embed(
        title="🐀 Your Ratburn Profile",
        description=(
            f"Here's what Ratburn has on file for {member.mention}."
        )
    )

    if profile["birthday_month"] and profile["birthday_day"]:
        birthday = (
            f"{calendar.month_name[profile['birthday_month']]} "
            f"{profile['birthday_day']}"
        )
    else:
        birthday = "Not provided"

    nickname = profile["nickname"] or member.display_name

    pronouns = "they/them"

    if profile["pronouns"]:
        try:
            pronoun_sets = json.loads(profile["pronouns"])

            if pronoun_sets:
                pronouns = " • ".join(
                    f"{item['subject']}/{item['object']}"
                    for item in pronoun_sets
                )
        except (json.JSONDecodeError, TypeError):
            pronouns = profile["pronouns"]

    timezone_name = profile["timezone"] or "Not provided"

    if profile["rules_acknowledged"]:
        rules = "✅ Acknowledged"
    else:
        rules = "❌ Not acknowledged"

    embed.add_field(
        name="🎂 Birthday",
        value=birthday,
        inline=True
    )

    embed.add_field(
        name="🏷️ Nickname",
        value=nickname,
        inline=True
    )

    embed.add_field(
        name="💬 Pronouns",
        value=pronouns,
        inline=True
    )

    embed.add_field(
        name="🌎 Timezone",
        value=timezone_name,
        inline=True
    )

    embed.add_field(
        name="📜 Rules",
        value=rules,
        inline=True
    )

    embed.add_field(
        name="🧠 Daily Quiz",
        value=f"**{profile['quiz_points']}** points",
        inline=True
    )

    embed.set_footer(
        text="Ratburn's got you on file. 🐀"
    )

    return embed


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="profile",
        description="View your Ratburn profile."
    )
    async def profile(
        self,
        interaction: discord.Interaction
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return

        profile = self.bot.database.get_member_profile(
            interaction.guild.id,
            interaction.user.id
        )

        embed = build_profile_embed(
            interaction.user,
            profile
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Profile(bot))
