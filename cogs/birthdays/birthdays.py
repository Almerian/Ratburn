import calendar
import logging
from datetime import datetime
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

            await self.run_birthday_cycle(
                guild,
                now
            )

    @birthday_loop.before_loop
    async def before_birthday_loop(self):
        await self.bot.wait_until_ready()

    async def run_birthday_cycle(
        self,
        guild: discord.Guild,
        now: datetime
    ):
        config = self.bot.database.get_config(guild.id)

        birthday_channel_id = config["birthday_channel_id"]

        if not birthday_channel_id:
            return

        birthday_channel = guild.get_channel(
            birthday_channel_id
        )

        if birthday_channel is None:
            return

        month = now.month
        day = now.day

        birthday_profiles = self.bot.database.get_birthdays(
            guild.id,
            month,
            day
        )

        if (
            month == 3
            and day == 1
            and not calendar.isleap(now.year)
        ):
            birthday_profiles += self.bot.database.get_birthdays(
                guild.id,
                2,
                29
            )

        birthday_members = []

        for profile in birthday_profiles:
            if profile["onboarding_step"] != "completed":
                continue

            member = guild.get_member(profile["user_id"])

            if member is None:
                continue

            birthday_members.append(
                (
                    member,
                    profile["nickname"]
                )
            )

        birthday_role = discord.utils.get(
            guild.roles,
            name="🎂 Birthday"
        )

        if birthday_members and birthday_role is None:
            try:
                birthday_role = await guild.create_role(
                    name="🎂 Birthday",
                    reason="Ratburn birthday role"
                )
            except discord.Forbidden:
                logger.error(
                    "Could not create birthday role in guild %s.",
                    guild.id
                )
                return
            except discord.HTTPException:
                logger.exception(
                    "Failed to create birthday role in guild %s.",
                    guild.id
                )
                return

        if birthday_role is not None:
            for member in list(birthday_role.members):
                try:
                    await member.remove_roles(
                        birthday_role,
                        reason="Birthday role refresh"
                    )
                except discord.Forbidden:
                    logger.error(
                        "Could not remove birthday role from %s in guild %s.",
                        member.id,
                        guild.id
                    )
                except discord.HTTPException:
                    logger.exception(
                        "Failed removing birthday role from %s in guild %s.",
                        member.id,
                        guild.id
                    )

        if not birthday_members:
            return

        for member, _ in birthday_members:
            try:
                await member.add_roles(
                    birthday_role,
                    reason="Birthday"
                )
            except discord.Forbidden:
                logger.error(
                    "Could not give birthday role to %s in guild %s.",
                    member.id,
                    guild.id
                )
            except discord.HTTPException:
                logger.exception(
                    "Failed giving birthday role to %s in guild %s.",
                    member.id,
                    guild.id
                )

        if len(birthday_members) == 1:
            member, nickname = birthday_members[0]

            nickname = nickname or member.display_name

            message = (
                "🎂 **It's someone's birthday!**\n\n"
                f"Everyone give {member.mention} some love — "
                f"Happy Birthday, **{nickname}**! 🎉\n"
                "Hope your day is an excellent one!"
            )

        else:
            birthday_lines = []

            for member, nickname in birthday_members:
                nickname = nickname or member.display_name

                birthday_lines.append(
                    f"- {member.mention} — **{nickname}**"
                )

            message = (
                "🎂 **I think there's some birthdays today!**\n\n"
                "Let's give some birthday love to:\n"
                + "\n".join(birthday_lines)
                + "\n\nHappy Birthday, everyone! 🎉"
            )

        try:
            await birthday_channel.send(message)
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
