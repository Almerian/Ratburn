import os
import logging
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import Database


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing.")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("ratburn")


class Ratburn(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents
        )

        self.database = Database()

    async def setup_hook(self):
        await self.load_extension("cogs.general")
        await self.load_extension("cogs.configuration")
        await self.load_extension("cogs.rat_trap")
        await self.load_extension("cogs.onboarding")
        await self.load_extension("cogs.new_member")
        await self.load_extension("cogs.profile")
        await self.load_extension("cogs.birthdays")
        await self.load_extension("cogs.events")
        await self.load_extension("cogs.daily_quiz")
        await self.load_extension("cogs.audit_logging")
        await self.load_extension("cogs.filter")
        await self.load_extension("cogs.discipline")
        await self.load_extension("cogs.ratburn_responses")

        logger.info(
            "Commands loaded: %s",
            [command.name for command in self.tree.get_commands()]
        )
                
        synced = await self.tree.sync()
        logger.info("Synced %s slash command(s).", len(synced))

    async def on_ready(self):
        logger.info(
            "Ratburn is online as %s (ID: %s)",
            self.user,
            self.user.id
        )

    async def close(self):
        self.database.close()
        await super().close()


from database import DATABASE_PATH

logger.info("Database file: %s", DATABASE_PATH.resolve())


bot = Ratburn()

bot.run(TOKEN)
