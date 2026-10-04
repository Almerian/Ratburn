import html
import logging

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


logger = logging.getLogger("ratburn.daily_quiz")


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
            "correct_answer": html.unescape(question["correct_answer"]),
            "incorrect_answers": [
                html.unescape(answer)
                for answer in question["incorrect_answers"]
            ],
            "category": html.unescape(question["category"]),
            "difficulty": question["difficulty"],
        }

    @app_commands.command(
        name="quiz_test",
        description="Test the Daily Quiz question fetch."
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

        await interaction.response.defer(ephemeral=True)

        question = await self.fetch_question()

        if question is None:
            await interaction.followup.send(
                "I couldn't get a question from OpenTDB.",
                ephemeral=True
            )
            return

        answers = [
            question["correct_answer"],
            *question["incorrect_answers"]
        ]

        embed = discord.Embed(
            title="🧠 Daily Quiz Test",
            description=question["question"],
            color=discord.Color.from_rgb(66, 135, 245)
        )

        for index, answer in enumerate(answers, start=1):
            embed.add_field(
                name=f"{index}.",
                value=answer,
                inline=False
            )

        embed.set_footer(
            text=(
                f"{question['category']} • "
                f"{question['difficulty'].title()}"
            )
        )

        try:
            await event_channel.send(
                embed=embed
            )
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
