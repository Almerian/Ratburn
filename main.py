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
    raise RuntimeError("DISCORD_TOKEN is missing from the .env file.")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("ratburn")


class Ratburn(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents
        )

        self.database = Database()

    async def setup_hook(self):
        await self.load_extension("cogs.general")

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


bot = Ratburn()

bot.run(TOKEN)
