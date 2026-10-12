import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import commands, tasks


logger = logging.getLogger("ratburn.events")


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminded_events = set()
        self.started_events = set()
        self.event_loop.start()

    def cog_unload(self):
        self.event_loop.cancel()

    @tasks.loop(minutes=1)
    async def event_loop(self):
        for guild in self.bot.guilds:
            config = self.bot.database.get_config(guild.id)

            if not config:
                continue

            if not config["events_enabled"]:
                continue

            event_channel_id = config["event_channel_id"]

            if not event_channel_id:
                continue

            event_channel = guild.get_channel(event_channel_id)

            if event_channel is None:
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

            for event in guild.scheduled_events:
                if event.status.name in ("cancelled", "completed"):
                    continue

                await self.check_event(
                    event,
                    event_channel,
                    timezone,
                    now
                )

    @event_loop.before_loop
    async def before_event_loop(self):
        await self.bot.wait_until_ready()

    async def check_event(
        self,
        event: discord.ScheduledEvent,
        event_channel: discord.TextChannel,
        timezone: ZoneInfo,
        now: datetime
    ):
        start_time = event.start_time.astimezone(timezone)
        time_until_start = start_time - now

        if (
            timedelta(hours=23, minutes=55)
            <= time_until_start
            <= timedelta(hours=24, minutes=5)
        ):
            if event.id not in self.reminded_events:
                success = await self.send_reminder(
                    event,
                    event_channel,
                    timezone
                )

                if success:
                    self.reminded_events.add(event.id)

        if (
            timedelta(minutes=-5)
            <= time_until_start
            <= timedelta(minutes=5)
        ):
            if event.id not in self.started_events:
                success = await self.send_start_announcement(
                    event,
                    event_channel
                )

                if success:
                    self.started_events.add(event.id)

    async def send_reminder(
        self,
        event: discord.ScheduledEvent,
        event_channel: discord.TextChannel,
        timezone: ZoneInfo
    ):
        start_time = event.start_time.astimezone(timezone)
        server_time = start_time.strftime("%I:%M %p").lstrip("0")
        discord_timestamp = int(event.start_time.timestamp())

        embed = discord.Embed(
            title="📅 Event Reminder!",
            description=(
                f"**{event.name}** is happening tomorrow at "
                f"**{server_time}!**\n\n"
                f"Or, **<t:{discord_timestamp}:t> for you!**\n\n"
                "Don't forget to join us!"
            ),
            color=discord.Color.from_rgb(66, 135, 245)
        )

        if event.url:
            embed.add_field(
                name="🔗 Event Link",
                value=event.url,
                inline=False
            )

        embed.set_footer(
            text="Ratburn's Event Department 🐀"
        )

        try:
            await event_channel.send(
                embed=embed
            )
            return True
        except discord.Forbidden:
            logger.error(
                "Could not send event reminder in guild %s.",
                event_channel.guild.id
            )
        except discord.HTTPException:
            logger.exception(
                "Failed sending event reminder in guild %s.",
                event_channel.guild.id
            )

        return False

    async def send_start_announcement(
        self,
        event: discord.ScheduledEvent,
        event_channel: discord.TextChannel
    ):
        embed = discord.Embed(
            title="🚨 It's Time!",
            description=(
                f"**{event.name}** is starting now!\n\n"
                "Come on in!"
            ),
            color=discord.Color.from_rgb(220, 53, 69)
        )

        if event.url:
            embed.add_field(
                name="🔗 Event Link",
                value=event.url,
                inline=False
            )

        embed.set_footer(
            text="Ratburn's Event Department 🐀"
        )

        try:
            await event_channel.send(
                embed=embed
            )
            return True
        except discord.Forbidden:
            logger.error(
                "Could not send event start announcement in guild %s.",
                event_channel.guild.id
            )
        except discord.HTTPException:
            logger.exception(
                "Failed sending event start announcement in guild %s.",
                event_channel.guild.id
            )

        return False


async def setup(bot):
    await bot.add_cog(Events(bot))
