import random
import time

import discord
from discord.ext import commands

from .defaults import RESPONSE_POOLS


COOLDOWN_SECONDS = 5 * 60


class RatburnResponses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    def get_matching_pools(self, content):
        words = set(
            word.strip(".,!?;:()[]{}\"'").lower()
            for word in content.split()
        )

        matches = []

        for pool_name, pool in RESPONSE_POOLS.items():
            if words.intersection(pool["triggers"]):
                matches.append(pool_name)

        return matches

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        pools = self.get_matching_pools(message.content)

        if not pools:
            return

        guild_id = message.guild.id if message.guild else None

        if guild_id is None:
            return

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
