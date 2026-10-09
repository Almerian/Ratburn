
import logging
import random
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord.ext import commands, tasks

from cogs.icebreaker.questions import get_builtin_questions


logger = logging.getLogger("ratburn.icebreaker")


class Icebreaker(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.daily_posting.start()

    async def cog_unload(self):
        self.daily_posting.cancel()

    @tasks.loop(minutes=1)
    async def daily_posting(self):
        """Check each server once per minute for its scheduled post."""

        for guild in self.bot.guilds:
            try:
                await self.post_for_guild(guild)
            except Exception:
                logger.exception(
                    "Unexpected error checking Icebreaker for guild %s.",
                    guild.id,
                )

    @daily_posting.before_loop
    async def before_daily_posting(self):
        await self.bot.wait_until_ready()

    async def post_for_guild(self, guild: discord.Guild):
        """Post today's question if this server is due."""

        db = self.bot.database
        config = db.get_config(guild.id)

        # Icebreaker is enabled by default.
        if not config["icebreaker_enabled"]:
            return

        channel_id = config["icebreaker_channel_id"]
        if not channel_id:
            return

        timezone_name = config["timezone"]
        if not timezone_name:
            logger.warning(
                "Icebreaker skipped for guild %s: no timezone configured.",
                guild.id,
            )
            return

        try:
            timezone = ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError):
            logger.warning(
                "Icebreaker skipped for guild %s: invalid timezone %r.",
                guild.id,
                timezone_name,
            )
            return

        now = datetime.now(timezone)
        today = now.date().isoformat()

        posting_time = config["icebreaker_posting_time"] or "09:00"

        try:
            scheduled_time = datetime.strptime(
                posting_time,
                "%H:%M",
            ).time()
        except ValueError:
            logger.warning(
                "Icebreaker skipped for guild %s: invalid posting time %r.",
                guild.id,
                posting_time,
            )
            return

        if now.time().replace(second=0, microsecond=0) < scheduled_time:
            return

        if db.has_icebreaker_posted(guild.id, today):
            return

        channel = guild.get_channel(channel_id)

        if channel is None:
            try:
                channel = await guild.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden):
                logger.warning(
                    "Icebreaker channel %s is unavailable in guild %s.",
                    channel_id,
                    guild.id,
                )
                return
            except discord.HTTPException:
                logger.exception(
                    "Could not fetch Icebreaker channel for guild %s.",
                    guild.id,
                )
                return

        if not hasattr(channel, "send"):
            logger.warning(
                "Configured Icebreaker channel %s cannot receive messages.",
                channel_id,
            )
            return

        questions = self.build_question_pool(guild.id)

        if not questions:
            logger.warning(
                "No Icebreaker questions available for guild %s.",
                guild.id,
            )
            return

        used_questions = db.get_icebreaker_used_questions(guild.id)
        available_questions = [
            question
            for question in questions
            if question["key"] not in used_questions
        ]

        if not available_questions:
            db.reset_icebreaker_question_usage(guild.id)
            available_questions = questions

        question = random.choice(available_questions)

        embed = discord.Embed(
            title="📚 Daily Icebreaker",
            description=question["text"],
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="A new conversation starter every day!")

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            logger.exception(
                "Failed to post Icebreaker for guild %s.",
                guild.id,
            )
            return

        # Only record the question after Discord confirms the send.
        db.mark_icebreaker_question_used(
            guild.id,
            question["key"],
        )
        db.record_icebreaker_post(
            guild.id,
            question["key"],
            question["text"],
            today,
        )

        logger.info(
            "Posted Icebreaker for guild %s on %s.",
            guild.id,
            today,
        )

    def build_question_pool(self, guild_id: int) -> list[dict[str, str]]:

        questions = [
            {
                "key": f"builtin:{question['id']}",
                "text": question["text"],
            }
            for question in get_builtin_questions()
        ]

        for question in self.bot.database.get_icebreaker_questions(guild_id):
            questions.append({
                "key": f"custom:{question['id']}",
                "text": question["question"],
            })

        return questions


async def setup(bot: commands.Bot):
    await bot.add_cog(Icebreaker(bot))
