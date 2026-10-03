import discord
from discord.ext import commands


class AuditLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_filter_violation(
        self,
        message: discord.Message,
        matched_word: str,
        action: str
    ):
        config = self.bot.database.get_config(
            message.guild.id
        )

        if config is None:
            return

        audit_channel_id = config["audit_log_channel_id"]

        if audit_channel_id is None:
            return

        audit_channel = message.guild.get_channel(
            audit_channel_id
        )

        if audit_channel is None:
            return

        content = message.content or "*[No text content]*"

        if len(content) > 4000:
            content = content[:3997] + "..."

        embed = discord.Embed(
            title="🚨 Chat Filter Violation",
            color=discord.Color.orange(),
            timestamp=message.created_at
        )

        embed.add_field(
            name="User",
            value=(
                f"{message.author.mention} "
                f"(`{message.author.id}`)"
            ),
            inline=False
        )

        embed.add_field(
            name="Triggered Filter",
            value=f"`{matched_word}`",
            inline=False
        )

        embed.add_field(
            name="Action",
            value=action.replace("_", " ").title(),
            inline=False
        )

        embed.add_field(
            name="Message",
            value=content,
            inline=False
        )

        embed.add_field(
            name="Channel",
            value=message.channel.mention,
            inline=False
        )

        try:
            await audit_channel.send(
                embed=embed
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            return


async def setup(bot):
    await bot.add_cog(AuditLogging(bot))
