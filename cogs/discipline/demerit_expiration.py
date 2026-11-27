import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from discord.ext import tasks


logger = logging.getLogger("ratburn.discipline")


def is_demerit_active(expires_at: str | None) -> bool:
    if expires_at is None:
        return True

    expiration_datetime = datetime.fromisoformat(expires_at)

    if expiration_datetime.tzinfo is None:
        expiration_datetime = expiration_datetime.replace(
            tzinfo=timezone.utc
        )

    return datetime.now(timezone.utc) < expiration_datetime


class DemeritExpirationManager:
    def __init__(self, bot):
        self.bot = bot
        self.last_sweep_dates = {}

        self.expiration_loop.start()

    @tasks.loop(minutes=1)
    async def expiration_loop(self):
        now_utc = datetime.now(timezone.utc)

        for guild in self.bot.guilds:
            try:
                config = self.bot.database.get_config(guild.id)

                if config is None:
                    continue

                timezone_name = config["timezone"]

                if not timezone_name:
                    logger.warning(
                        "Demerit expiration sweep skipped for guild %s: "
                        "no timezone configured.",
                        guild.id,
                    )
                    continue

                try:
                    server_timezone = ZoneInfo(timezone_name)
                except (ZoneInfoNotFoundError, ValueError):
                    logger.error(
                        "Invalid timezone '%s' configured for guild %s. "
                        "Demerit expiration sweep skipped.",
                        timezone_name,
                        guild.id,
                    )
                    continue

                local_now = now_utc.astimezone(server_timezone)
                sweep_date = local_now.date().isoformat()

                # Run at 12:01 AM or later if the loop was delayed.
                if (
                    local_now.hour != 0
                    or local_now.minute < 1
                ):
                    continue

                # Only sweep once per local calendar day.
                if self.last_sweep_dates.get(guild.id) == sweep_date:
                    continue

                expired_count = (
                    self.bot.database.mark_expired_demerits(guild.id)
                )

                self.last_sweep_dates[guild.id] = sweep_date

                logger.info(
                    "Demerit expiration sweep completed for guild %s. "
                    "Marked %s demerit(s) expired.",
                    guild.id,
                    expired_count,
                )

            except Exception:
                logger.exception(
                    "Unexpected error during demerit expiration sweep "
                    "for guild %s.",
                    guild.id,
                )

    @expiration_loop.before_loop
    async def before_expiration_loop(self):
        await self.bot.wait_until_ready()

        # Catch up on expired demerits from while Ratburn was offline.
        try:
            expired_count = (
                self.bot.database.mark_expired_demerits()
            )

            logger.info(
                "Startup demerit expiration catch-up completed. "
                "Marked %s demerit(s) expired.",
                expired_count,
            )

        except Exception:
            logger.exception(
                "Failed to complete startup demerit expiration catch-up."
            )

    def stop(self):
        self.expiration_loop.cancel()
