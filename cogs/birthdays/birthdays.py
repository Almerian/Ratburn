import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import commands, tasks


logger = logging.getLogger("ratburn.birthdays")


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_loop.start()

    def cog_unload(self):
        self.birthday_loop.cancel()

    @tasks.loop(minutes=1)
    async def birthday_loop(self):
        for guild in self.bot.guilds:
            config = self.bot.database.get_config(guild.id)

            if not config:
                continue

            birthday_channel_id = config["birthday_channel_id"]

            if not birthday_channel_id:
                continue

            birthday_channel = guild.get_channel(birthday_channel_id)

            if birthday_channel is None:
                continue

            timezone_name = config["timezone"]

            if not timezone_name:
                continue

            try:
                timezone = ZoneInfo(timezone_name)
            except ZoneInfoNotFoundError:
                logger.error(
                    "Invalid timezone configured for guild %s: %s",
                    guild.id,
                    timezone_name
                )
                continue

            now = datetime.now(timezone)

            if now.hour != 12 or now.minute != 0:
                continue

            await self.handle_birthdays(
                guild,
                birthday_channel,
                now
            )

    @birthday_loop.before_loop
    async def before_birthday_loop(self):
        await self.bot.wait_until_ready()

    async def handle_birthdays(
        self,
        guild: discord.Guild,
        birthday_channel: discord.TextChannel,
        now: datetime
    ):
        birthdays = self.bot.database.get_birthdays(
            guild.id,
            now.month,
            now.day
        )

        if now.month == 3 and now.day == 1:
            birthdays.extend(
                self.bot.database.get_birthdays(
                    guild.id,
                    2,
                    29
                )
            )

        if not birthdays:
            return

        birthday_role = discord.utils.get(
            guild.roles,
            name="🎂 Birthday"
        )

        if birthday_role is None:
            try:
                birthday_role = await guild.create_role(
                    name="🎂 Birthday"
                )
            except discord.Forbidden:
                logger.error(
                    "Could not create birthday role in guild %s.",
                    guild.id
                )
                return
            except discord.HTTPException:
                logger.exception(
                    "Failed creating birthday role in guild %s.",
                    guild.id
                )
                return

        birthday_members = []

        for birthday in birthdays:
            member = guild.get_member(birthday["user_id"])

            if member is None:
                continue

            birthday_members.append(
                (member, birthday["nickname"])
            )

            try:
                await member.add_roles(birthday_role)
            except discord.Forbidden:
                logger.error(
                    "Could not assign birthday role to %s in guild %s.",
                    member,
                    guild.id
                )
            except discord.HTTPException:
                logger.exception(
                    "Failed assigning birthday role to %s in guild %s.",
                    member,
                    guild.id
                )

        if not birthday_members:
            return

        if len(birthday_members) == 1:
            member, nickname = birthday_members[0]

            embed = discord.Embed(
                title="🎂 Birthday Time!",
                description=(
                    f"Everyone give **{member.mention}** some love — "
                    f"Happy Birthday, **{nickname}**! 🎉\n\n"
                    "Hope your day is an excellent one!"
                ),
                color=discord.Color.from_rgb(255, 193, 7)
            )
        else:
            birthday_lines = []

            for member, nickname in birthday_members:
                birthday_lines.append(
                    f"🎉 **{member.mention}** — {nickname}"
                )

            embed = discord.Embed(
                title="🎂 Birthday Time!",
                description=(
                    "Let's give some birthday love to:\n\n"
                    + "\n".join(birthday_lines)
                    + "\n\nHappy Birthday, everyone! 🎉"
                ),
                color=discord.Color.from_rgb(255, 193, 7)
            )

        embed.set_footer(
            text="Ratburn's Birthday Department 🐀"
        )

        try:
            await birthday_channel.send(
                embed=embed
            )
        except discord.Forbidden:
            logger.error(
                "Could not send birthday announcement in guild %s.",
                guild.id
            )
        except discord.HTTPException:
            logger.exception(
                "Failed sending birthday announcement in guild %s.",
                guild.id
            )


async def setup(bot):
    await bot.add_cog(Birthdays(bot))
