import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta

from .demerit_expiration import is_demerit_active
from .thresholds import get_punishment_tier
from .mute import issue_mute
from .detention import DetentionManager
from .ban import issue_ban


class Discipline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.detention = DetentionManager(bot)

#==================================DO NOT REMOVE==================================
    @commands.hybrid_command(
        name="discipline_clear",
        description="Clear all discipline records for a user."
    )
    @app_commands.describe(
        user="The user whose discipline records should be cleared."
    )
    @app_commands.default_permissions(administrator=True)
    async def discipline_clear(
        self,
        ctx: commands.Context,
        user: discord.Member
    ):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "Sorry, you need to be an administrator for that!",
                ephemeral=True
            )
            return

        self.bot.database.clear_discipline_records(
            ctx.guild.id,
            user.id
        )

        await ctx.send(
            f"Cleared all discipline records for {user.mention}.",
            ephemeral=True
        )

#==================================DO NOT REMOVE==================================
    @commands.hybrid_command(
        name="discipline_detain",
        description="Place a user in detention for testing."
    )
    @app_commands.describe(
        user="The user to place in detention."
    )
    @app_commands.default_permissions(administrator=True)
    async def discipline_detain(
        self,
        ctx: commands.Context,
        user: discord.Member
    ):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "Sorry, you need to be an administrator for that!",
                ephemeral=True
            )
            return

        success, message = await self.detention.issue_detention(
            ctx.guild.id,
            user.id,
            "manual_test"
        )

        await ctx.send(
            message,
            ephemeral=True
        )

    def cog_unload(self):
        self.detention.stop()

    async def process_violation(
        self,
        guild_id: int,
        user_id: int,
        reason: str
    ) -> str:
        records = self.bot.database.get_active_discipline_records(
            guild_id,
            user_id
        )

        discipline_config = self.bot.database.get_discipline_config(
            guild_id
        )

        has_previous_discipline = bool(records)

        active_demerits = []

        for record in records:
            if record["action"] != "demerit":
                continue

            if is_demerit_active(
                record["expires_at"]
            ):
                active_demerits.append(record)

        if not has_previous_discipline:
            self.bot.database.add_discipline_record(
                guild_id,
                user_id,
                "warning",
                reason
            )
            return "warning"

        expires_at = None

        if discipline_config is not None:
            expiration_value = (
                discipline_config["demerit_expiration_value"]
            )
            expiration_unit = (
                discipline_config["demerit_expiration_unit"]
            )

            if (
                expiration_value is not None
                and expiration_unit is not None
                and expiration_unit != "never"
            ):
                now = datetime.now(timezone.utc)

                if expiration_unit == "days":
                    expires_at = now + timedelta(
                        days=expiration_value
                    )

                elif expiration_unit == "weeks":
                    expires_at = now + timedelta(
                        weeks=expiration_value
                    )

                elif expiration_unit == "months":
                    expires_at = now + timedelta(
                        days=expiration_value * 30
                    )

                if expires_at is not None:
                    expires_at = expires_at.isoformat()

        self.bot.database.add_discipline_record(
            guild_id,
            user_id,
            "demerit",
            reason,
            expires_at
        )

        active_demerit_count = len(active_demerits) + 1

        punishment_tier = get_punishment_tier(
            active_demerit_count,
            discipline_config
        )

        guild = self.bot.get_guild(guild_id)

        if guild is None:
            return "demerit"

        member = guild.get_member(user_id)

        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound:
                return "demerit"
            except discord.Forbidden:
                return "demerit"
            except discord.HTTPException:
                return "demerit"

        if punishment_tier == "mute":
            duration_value = discipline_config["mute_duration_value"]
            duration_unit = discipline_config["mute_duration_unit"]

            success, message = await issue_mute(
                member,
                duration_value,
                duration_unit
            )

            if success:
                self.bot.database.add_discipline_record(
                    guild_id,
                    user_id,
                    "mute",
                    reason
                )
                return "mute"

            return "demerit"

        if punishment_tier == "detention":
            success, _ = await self.detention.issue_detention(
                guild_id,
                user_id,
                reason
            )

            if success:
                return "detention"

            return "demerit"

        if punishment_tier == "ban":
            success, _ = await issue_ban(member)

            if success:
                self.bot.database.add_discipline_record(
                    guild_id,
                    user_id,
                    "ban",
                    reason
                )
                return "ban"

            return "demerit"

        return punishment_tier


async def setup(bot):
    await bot.add_cog(Discipline(bot))
