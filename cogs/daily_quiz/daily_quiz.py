import html
import logging
import random
import sqlite3

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


logger = logging.getLogger("ratburn.daily_quiz")


class QuizButton(discord.ui.Button):
    def __init__(
        self,
        quiz_view,
        answer: str,
        correct: bool,
        position: int
    ):
        super().__init__(
            label=f"{position}. {answer}",
            style=discord.ButtonStyle.primary
        )

        self.quiz_view = quiz_view
        self.answer = answer
        self.correct = correct

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This quiz can only be answered inside a server.",
                ephemeral=True
            )
            return

        quiz_date = self.quiz_view.quiz_date

        if self.quiz_view.bot.database.has_answered_quiz(
            guild.id,
            interaction.user.id,
            quiz_date
        ):
            await interaction.response.send_message(
                "You've already answered today's quiz! "
                "Come back tomorrow for the next one. 🐀",
                ephemeral=True
            )
            return

        try:
            self.quiz_view.bot.database.record_quiz_answer(
                guild.id,
                interaction.user.id,
                quiz_date,
                self.correct
            )
        except sqlite3.IntegrityError:
            await interaction.response.send_message(
                "You've already answered today's quiz! "
                "Come back tomorrow for the next one. 🐀",
                ephemeral=True
            )
            return

        if self.correct:
            self.quiz_view.bot.database.add_quiz_point(
                guild.id,
                interaction.user.id
            )

            score = self.quiz_view.bot.database.get_quiz_score(
                guild.id,
                interaction.user.id
            )

            await interaction.response.send_message(
                f"✅ **Correct!** Nice work!\n\n"
                f"You earned **1 point**. Your total score is now "
                f"**{score}**.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ **Not quite!** Better luck tomorrow! 🐀",
                ephemeral=True
            )


class QuizView(discord.ui.View):
    def __init__(
        self,
        bot,
        quiz_date: str,
        answers: list[tuple[str, bool]]
    ):
        super().__init__(timeout=21600)

        self.bot = bot
        self.quiz_date = quiz_date
        self.message = None

        for position, (answer, correct) in enumerate(
            answers,
            start=1
        ):
            self.add_item(
                QuizButton(
                    self,
                    answer,
                    correct,
                    position
                )
            )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass
            except discord.HTTPException:
                logger.exception(
                    "Failed disabling expired quiz buttons."
                )


class DailyQuiz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_question(self):
        url = "https://opentdb.com/api.php?amount=1&type=multiple"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(
                        "OpenTDB returned HTTP status %s.",
                        response.status
                    )
                    return None

                data = await response.json()

        if data.get("response_code") != 0:
            logger.error(
                "OpenTDB returned response code %s.",
                data.get("response_code")
            )
            return None

        question = data["results"][0]

        return {
            "question": html.unescape(question["question"]),
            "correct_answer": html.unescape(
                question["correct_answer"]
            ),
            "incorrect_answers": [
                html.unescape(answer)
                for answer in question["incorrect_answers"]
            ],
            "category": html.unescape(question["category"]),
            "difficulty": question["difficulty"],
        }

    @app_commands.command(
        name="quiz_test",
        description="Test the Daily Quiz."
    )
    @app_commands.default_permissions(administrator=True)
    async def quiz_test(
        self,
        interaction: discord.Interaction
    ):
        config = self.bot.database.get_config(interaction.guild.id)

        if not config:
            await interaction.response.send_message(
                "Ratburn couldn't load this server's configuration.",
                ephemeral=True
            )
            return

        event_channel_id = config["event_channel_id"]

        if not event_channel_id:
            await interaction.response.send_message(
                "No Event Channel is configured.",
                ephemeral=True
            )
            return

        event_channel = interaction.guild.get_channel(
            event_channel_id
        )

        if event_channel is None:
            await interaction.response.send_message(
                "The configured Event Channel could not be found.",
                ephemeral=True
            )
            return

        timezone_name = config["timezone"]

        if not timezone_name:
            await interaction.response.send_message(
                "No server timezone is configured.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        question = await self.fetch_question()

        if question is None:
            await interaction.followup.send(
                "I couldn't get a question from OpenTDB.",
                ephemeral=True
            )
            return

        import datetime
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            await interaction.followup.send(
                "The server's configured timezone is invalid.",
                ephemeral=True
            )
            return

        quiz_date = datetime.datetime.now(timezone).date().isoformat()

        answers = [
            (
                question["correct_answer"],
                True
            ),
            *[
                (answer, False)
                for answer in question["incorrect_answers"]
            ]
        ]

        random.shuffle(answers)

        embed = discord.Embed(
            title="🧠 Daily Quiz Test",
            description=question["question"],
            color=discord.Color.from_rgb(66, 135, 245)
        )

        embed.set_footer(
            text=(
                f"{question['category']} • "
                f"{question['difficulty'].title()}"
            )
        )

        view = QuizView(
            self.bot,
            quiz_date,
            answers
        )

        try:
            message = await event_channel.send(
                embed=embed,
                view=view
            )
            view.message = message
        except discord.Forbidden:
            await interaction.followup.send(
                "I don't have permission to post in the Event Channel.",
                ephemeral=True
            )
            return
        except discord.HTTPException:
            logger.exception(
                "Failed posting Daily Quiz test in guild %s.",
                interaction.guild.id
            )
            await interaction.followup.send(
                "Something went wrong while posting the test question.",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            f"Test question posted in {event_channel.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(DailyQuiz(bot))
