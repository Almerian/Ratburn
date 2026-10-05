import logging

import discord
from discord.ext import commands


logger = logging.getLogger("ratburn.new_member")


class NewMember(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_new_member_role(
        self,
        guild: discord.Guild
    ):
        role = discord.utils.get(
            guild.roles,
            name="✨ New Member"
        )

        if role is not None:
            return role

        try:
            role = await guild.create_role(
                name="✨ New Member"
            )
        except discord.Forbidden:
            logger.error(
                "Could not create New Member role in guild %s.",
                guild.id
            )
            return None
        except discord.HTTPException:
            logger.exception(
                "Failed creating New Member role in guild %s.",
                guild.id
            )
            return None

        logger.info(
            "Created New Member role in guild %s.",
            guild.id
        )

        return role

        async def remove_new_member_role(
            self,
            member: discord.Member
        ):
            role = discord.utils.get(
                member.guild.roles,
                name="✨ New Member"
            )
    
            if role is None:
                return
    
            if role not in member.roles:
                return
    
            try:
                await member.remove_roles(
                    role,
                    reason="Rules acknowledged"
                )
            except discord.Forbidden:
                logger.error(
                    "Could not remove New Member role from %s in guild %s.",
                    member.id,
                    member.guild.id
                )
            except discord.HTTPException:
                logger.exception(
                    "Failed removing New Member role from %s in guild %s.",
                    member.id,
                    member.guild.id
                )

    async def configure_channel_permissions(
        self,
        guild: discord.Guild
    ):
        role = await self.ensure_new_member_role(guild)

        if role is None:
            return

        config = self.bot.database.get_config(guild.id)

        if config is None:
            return

        welcome_channel_id = config["welcome_channel_id"]
        rat_trap_channel_id = config["rat_trap_channel_id"]

        staff_role = (
            guild.get_role(config["staff_role_id"])
            if config["staff_role_id"]
            else None
        )

        for channel in guild.channels:
            try:
                if channel.id == welcome_channel_id:
                    await channel.set_permissions(
                        role,
                        view_channel=True
                    )

                    await channel.set_permissions(
                        guild.default_role,
                        send_messages=False
                    )

                    if staff_role is not None:
                        await channel.set_permissions(
                            staff_role,
                            view_channel=True,
                            send_messages=True
                        )

                    if guild.me is not None:
                        await channel.set_permissions(
                            guild.me,
                            view_channel=True,
                            send_messages=True
                        )

                elif channel.id == rat_trap_channel_id:
                    await channel.set_permissions(
                        role,
                        view_channel=True
                    )

                else:
                    await channel.set_permissions(
                        role,
                        view_channel=False
                    )

            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                continue

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.configure_channel_permissions(guild)

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member
    ):
        role = await self.ensure_new_member_role(
            member.guild
        )

        if role is None:
            return

        try:
            await member.add_roles(
                role,
                reason="New member onboarding"
            )
        except discord.Forbidden:
            logger.error(
                "Could not give New Member role to %s in guild %s.",
                member.id,
                member.guild.id
            )
        except discord.HTTPException:
            logger.exception(
                "Failed giving New Member role to %s in guild %s.",
                member.id,
                member.guild.id
            )


async def setup(bot):
    await bot.add_cog(NewMember(bot))
