import random
import re
import time

import discord
from discord.ext import commands

from .defaults import RESPONSE_POOLS


COOLDOWN_SECONDS = 5 * 60


def normalize_words(text: str) -> list[str]:
    """Return lowercase word tokens, ignoring surrounding punctuation."""
    return re.findall(r"\w+", text.casefold())


def contains_trigger(content: str, trigger: str) -> bool:
    """Match a trigger as a whole word or consecutive sequence of words."""
    content_words = normalize_words(content)
    trigger_words = normalize_words(trigger)

    if not trigger_words or len(trigger_words) > len(content_words):
        return False

    length = len(trigger_words)

    return any(
        content_words[index:index + length] == trigger_words
        for index in range(len(content_words) - length + 1)
    )


class RatburnResponses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    def get_matching_pools(self, content):
        matches = []

        for pool_name, pool in RESPONSE_POOLS.items():
            triggers = pool.get("triggers", [])

            if any(
                contains_trigger(content, trigger)
                for trigger in triggers
            ):
                matches.append(pool_name)

        return matches

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        config = self.bot.database.get_config(message.guild.id)

        if not config["ratburn_responses_enabled"]:
            return

        pools = self.get_matching_pools(message.content)

        if not pools:
            return

        guild_id = message.guild.id
        current_time = time.monotonic()
        cooldown_until = self.cooldowns.get(guild_id, 0)

        if current_time < cooldown_until:
            return

        pool_name = random.choice(pools)
        response = random.choice(
            RESPONSE_POOLS[pool_name]["responses"]
        )

        await message.channel.send(response)

        self.cooldowns[guild_id] = (
            current_time + COOLDOWN_SECONDS
        )


async def setup(bot):
    await bot.add_cog(RatburnResponses(bot))
