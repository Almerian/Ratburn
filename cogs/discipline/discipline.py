import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta

from .demerit_expiration import is_demerit_active
from .thresholds import get_punishment_tier
from .mute import issue_mute
from .detention import DetentionManager
from .ban import issue_ban
from .discipline_view import DisciplineRecordView


class Discipline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.detention = DetentionManager(bot)


    
    @commands.hybrid_command(
        name="discipline",
        description="View or manage a member's discipline record."
    )
    @app_commands.describe(
        name="The member whose discipline record you want to view or manage.",
        clear="Clear all discipline records for this member.",
        detain="Place this member in detention."
    )
    @app_commands.default_permissions(administrator=True)
    async def discipline(
        self,
        ctx: commands.Context,
        name: discord.Member,
        clear: bool = False,
        detain: bool = False
    ):
        if ctx.guild is None:
            await ctx.send(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "Sorry, you need to be an administrator for that!",
                ephemeral=True
            )
            return

        if clear and detain:
            await ctx.send(
                "Please choose either `clear` or `detain`, not both.",
                ephemeral=True
            )
            return

        if clear:
            self.bot.database.clear_discipline_records(
                ctx.guild.id,
                name.id
            )

            await ctx.send(
                f"Cleared all discipline records for {name.mention}.",
                ephemeral=True
            )
            return

        if detain:
            success, message = await self.detention.issue_detention(
                ctx.guild.id,
                name.id,
                "manual"
            )

            await ctx.send(
                message,
                ephemeral=True
            )
            return

        database = self.bot.database
        guild_id = ctx.guild.id
        user_id = name.id

        active_records = database.get_active_discipline_records(
            guild_id,
            user_id
        )

        retired_records = database.get_retired_discipline_records(
            guild_id,
            user_id
        )

        active_records = [
            record
            for record in active_records
            if (
                record["action"] != "demerit"
                or is_demerit_active(record["expires_at"])
            )
        ]

        active_demerits = sum(
            1
            for record in active_records
            if record["action"] == "demerit"
        )

        lifetime_demerits = database.get_lifetime_demerit_count(
            guild_id,
            user_id
        )

        discipline_config = database.get_discipline_config(
            guild_id
        )

        if discipline_config is None:
            punishment_tier = "Demerit"
        else:
            punishment_tier = get_punishment_tier(
                active_demerits,
                discipline_config
            )

            punishment_tier = str(
                punishment_tier
            ).replace("_", " ").title()

        view = DisciplineRecordView(
            owner_id=ctx.author.id,
            member=name,
            active_records=active_records,
            retired_records=retired_records,
            active_demerits=active_demerits,
            lifetime_demerits=lifetime_demerits,
            punishment_tier=punishment_tier,
        )

        await ctx.send(
            embed=view.build_embed(),
            view=view,
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
