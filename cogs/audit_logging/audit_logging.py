import asyncio
from collections import OrderedDict

import discord
from discord.ext import commands


class AuditLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_cache = OrderedDict()
        self.message_cache_limit = 5000

    def cache_message(self, message: discord.Message):
        if message.guild is None:
            return

        self.message_cache[message.id] = message
        self.message_cache.move_to_end(message.id)

        while len(self.message_cache) > self.message_cache_limit:
            self.message_cache.popitem(last=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        self.cache_message(message)

    async def get_audit_channel(self, guild: discord.Guild):
        config = self.bot.database.get_config(guild.id)

        if config is None:
            return None

        audit_channel_id = config["audit_log_channel_id"]

        if audit_channel_id is None:
            return None

        return guild.get_channel(audit_channel_id)

    async def find_message_deleter(
        self,
        guild: discord.Guild,
        message: discord.Message,
        deleted_at
    ):
        if message.author is None:
            return None

        # Give Discord a moment to register the audit-log entry.
        await asyncio.sleep(1)

        try:
            async for entry in guild.audit_logs(
                limit=10,
                action=discord.AuditLogAction.message_delete
            ):
                if entry.target is None:
                    continue

                if entry.target.id != message.author.id:
                    continue

                if entry.extra is None:
                    continue

                if entry.extra.channel.id != message.channel.id:
                    continue

                age = abs(
                    (deleted_at - entry.created_at).total_seconds()
                )

                if age <= 10:
                    return entry.user

        except (
            discord.Forbidden,
            discord.HTTPException,
            AttributeError
        ):
            return None

        return None

    async def log_deleted_message(
        self,
        guild: discord.Guild,
        message: discord.Message | None,
        channel: discord.abc.GuildChannel | discord.Thread | None,
        deleted_at
    ):
        audit_channel = await self.get_audit_channel(guild)

        if audit_channel is None:
            return

        if channel is not None and channel.id == audit_channel.id:
            return

        if message is not None and message.author.bot:
            return

        if message is not None:
            author = message.author
            content = message.content or "*[No text content]*"
            posted_at = message.created_at

            if len(content) > 4000:
                content = content[:3997] + "..."

            attachments = [
                attachment.url
                for attachment in message.attachments
            ]
        else:
            author = None
            content = (
                "*[Message content unavailable — "
                "the message was not cached]*"
            )
            posted_at = None
            attachments = []

        deleter = None

        if message is not None:
            deleter = await self.find_message_deleter(
                guild,
                message,
                deleted_at
            )

        embed = discord.Embed(
            title="🗑️ Deleted Message",
            description=content,
            color=discord.Color.red(),
            timestamp=deleted_at
        )

        embed.add_field(
            name="Posted by",
            value=(
                f"{author.mention} (`{author.id}`)"
                if author is not None
                else "*Unknown — message was not cached*"
            ),
            inline=False
        )

        embed.add_field(
            name="Posted at",
            value=(
                f"<t:{int(posted_at.timestamp())}:F>"
                if posted_at is not None
                else "*Unknown*"
            ),
            inline=False
        )

        embed.add_field(
            name="Deleted by",
            value=(
                f"{deleter.mention} (`{deleter.id}`)"
                if deleter is not None
                else "*Unknown — Discord did not provide a matching audit-log entry*"
            ),
            inline=False
        )

        embed.add_field(
            name="Deleted at",
            value=f"<t:{int(deleted_at.timestamp())}:F>",
            inline=False
        )

        embed.add_field(
            name="Channel",
            value=channel.mention if channel is not None else "*Unknown*",
            inline=False
        )

        if attachments:
            attachment_text = "\n".join(attachments)
            if len(attachment_text) > 1000:
                attachment_text = attachment_text[:997] + "..."

            embed.add_field(
                name="Attachments",
                value=attachment_text,
                inline=False
            )

        try:
            await audit_channel.send(embed=embed)

        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            return
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        self.cache_message(after)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.message_cache.pop(message.id, None)
        
    @commands.Cog.listener()
    async def on_raw_message_delete(
        self,
        payload: discord.RawMessageDeleteEvent
    ):
        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)

        if guild is None:
            return

        channel = guild.get_channel(payload.channel_id)

        message = payload.cached_message

        if message is None:
            message = self.message_cache.get(payload.message_id)

        self.message_cache.pop(payload.message_id, None)
        
        if message is not None and message.author.id == self.bot.user.id:
            return

        await self.log_deleted_message(
            guild=guild,
            message=message,
            channel=channel,
            deleted_at=discord.utils.utcnow()
        )

    async def log_filter_violation(
        self,
        message: discord.Message,
        matched_word: str,
        action: str
    ):
        config = self.bot.database.get_config(
            message.guild.id
        )

        if config is None:
            return

        audit_channel_id = config["audit_log_channel_id"]

        if audit_channel_id is None:
            return

        audit_channel = message.guild.get_channel(
            audit_channel_id
        )

        if audit_channel is None:
            return

        content = message.content or "*[No text content]*"

        if len(content) > 4000:
            content = content[:3997] + "..."

        embed = discord.Embed(
            title="🚨 Chat Filter Violation",
            color=discord.Color.orange(),
            timestamp=message.created_at
        )

        embed.add_field(
            name="User",
            value=(
                f"{message.author.mention} "
                f"(`{message.author.id}`)"
            ),
            inline=False
        )

        embed.add_field(
            name="Triggered Filter",
            value=f"`{matched_word}`",
            inline=False
        )

        embed.add_field(
            name="Action",
            value=action.replace("_", " ").title(),
            inline=False
        )

        embed.add_field(
            name="Message",
            value=content,
            inline=False
        )

        embed.add_field(
            name="Channel",
            value=message.channel.mention,
            inline=False
        )

        try:
            await audit_channel.send(
                embed=embed
            )

        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            return


async def setup(bot):
    await bot.add_cog(AuditLogging(bot))
