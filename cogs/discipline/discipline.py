import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone, timedelta
from .demerit_expiration import is_demerit_active
from .thresholds import get_punishment_tier

class Discipline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.detention_expiry_loop.start()
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

        success, message = await self.issue_detention(
            ctx.guild.id,
            user.id,
            "manual_test"
        )

        await ctx.send(
            message,
            ephemeral=True
        )
#==================================DO NOT REMOVE==================================
    async def issue_detention(
        self,
        guild_id: int,
        user_id: int,
        reason: str
    ):
        guild = self.bot.get_guild(guild_id)

        if guild is None:
            return False, "I couldn't find that server."

        config = self.bot.database.get_config(
            guild_id
        )

        if config is None:
            return False, "The server configuration could not be found."

        detention_role_id = config["detention_role_id"]

        if detention_role_id is None:
            return False, "No detention role has been configured."

        detention_role = guild.get_role(
            detention_role_id
        )

        if detention_role is None:
            return False, "The configured detention role no longer exists."

        member = guild.get_member(user_id)

        if member is None:
            return False, "I couldn't find that member."

        discipline_config = self.bot.database.get_discipline_config(
            guild_id
        )

        if discipline_config is None:
            return False, "Detention duration has not been configured."

        duration_value = discipline_config[
            "detention_duration_value"
        ]

        duration_unit = discipline_config[
            "detention_duration_unit"
        ]

        if duration_value is None or duration_unit is None:
            return False, "Detention duration has not been configured."

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
            return False, "The configured detention duration is invalid."

        expires_at = datetime.now(
            timezone.utc
        ) + duration

        try:
            await member.add_roles(
                detention_role,
                reason="Disciplinary detention"
            )

        except discord.Forbidden:
            return (
                False,
                "I don't have permission to assign the detention role."
            )

        except discord.HTTPException:
            return (
                False,
                "Discord rejected the detention role assignment."
            )

        self.bot.database.add_discipline_record(
            guild_id,
            user_id,
            "detention",
            reason,
            expires_at.isoformat()
        )

        return (
            True,
            f"{member.mention} has been placed in detention "
            f"for {duration_value} {duration_unit}."
        )

    @tasks.loop(minutes=1)
    async def detention_expiry_loop(self):
        expired_detentions = (
            self.bot.database.get_expired_detentions()
        )

        for record in expired_detentions:
            guild = self.bot.get_guild(
                record["guild_id"]
            )

            if guild is None:
                continue

            config = self.bot.database.get_config(
                record["guild_id"]
            )

            if config is None:
                continue

            detention_role_id = config["detention_role_id"]

            if detention_role_id is None:
                self.bot.database.expire_discipline_record(
                    record["id"]
                )
                continue

            role = guild.get_role(
                detention_role_id
            )

            if role is None:
                self.bot.database.expire_discipline_record(
                    record["id"]
                )
                continue

            member = guild.get_member(
                record["user_id"]
            )

            if member is None:
                self.bot.database.expire_discipline_record(
                    record["id"]
                )
                continue

            try:
                if role in member.roles:
                    await member.remove_roles(
                        role,
                        reason="Detention expired"
                    )

                self.bot.database.expire_discipline_record(
                    record["id"]
                )

            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                continue

    @detention_expiry_loop.before_loop
    async def before_detention_expiry_loop(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.detention_expiry_loop.cancel()

    def process_violation(
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
    
        expiration_value = None
        expiration_unit = None
    
        if discipline_config is not None:
            expiration_value = discipline_config[
                "demerit_expiration_value"
            ]
    
            expiration_unit = discipline_config[
                "demerit_expiration_unit"
            ]
    
        active_demerits = []
    
        for record in records:
            if record["action"] != "demerit":
                continue
    
            if is_demerit_active(
                record["created_at"],
                expiration_value,
                expiration_unit
            ):
                active_demerits.append(record)
    
        if not active_demerits:
            self.bot.database.add_discipline_record(
                guild_id,
                user_id,
                "warning",
                reason
            )
    
            return "warning"
    
        self.bot.database.add_discipline_record(
            guild_id,
            user_id,
            "demerit",
            reason
        )
    
        active_demerit_count = len(active_demerits) + 1
    
        return get_punishment_tier(
            active_demerit_count,
            discipline_config
        )


async def setup(bot):
    await bot.add_cog(Discipline(bot))
