import calendar
import json
import logging
import re
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
import holidays
from discord import app_commands
from discord.ext import commands, tasks

logger = logging.getLogger("ratburn.monthly_calendar")

POST_TIME = time(hour=0, minute=1)
EDIT_WINDOW = timedelta(hours=24)
MAX_SELECT_OPTIONS = 25

COMMON_COUNTRIES = {
    "US": "United States",
    "CA": "Canada",
    "GB": "United Kingdom",
    "RU": "Russia",
    "ES": "Spain",
    "JP": "Japan",
    "AU": "Australia",
    "NZ": "New Zealand",
    "IE": "Ireland",
    "FR": "France",
    "DE": "Germany",
    "IT": "Italy",
    "MX": "Mexico",
    "BR": "Brazil",
    "IN": "India",
    "CN": "China",
    "KR": "South Korea",
    "NL": "Netherlands",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "ZA": "South Africa",
}

COMMON_OBSERVANCES = {
    (1, 1): "New Year's Day",
    (2, 14): "Valentine's Day",
    (10, 31): "Halloween",
    (12, 31): "New Year's Eve",
}


def parse_regions(raw_value) -> list[str]:
    if not raw_value:
        return ["US"]

    try:
        regions = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return ["US"]

    if not isinstance(regions, list):
        return ["US"]

    normalized = []
    for region in regions:
        if isinstance(region, str):
            region = region.strip().upper()
            if region and region not in normalized:
                normalized.append(region)

    return normalized or ["US"]


@lru_cache(maxsize=48)
def get_holidays_cached(year: int, regions: tuple[str, ...]) -> dict[date, tuple[str, ...]]:
    result: dict[date, list[str]] = {}

    def add(day: date, name: str):
        names = result.setdefault(day, [])
        if name not in names:
            names.append(name)

    international = any(
        region in {"INTL", "INTERNATIONAL", "ALL"}
        for region in regions
    )
    selected = set(COMMON_COUNTRIES) if international else set(regions)

    if international:
        try:
            selected.update(holidays.list_supported_countries().keys())
        except Exception:
            logger.exception("Could not enumerate supported holiday countries.")

    for country_code in sorted(selected):
        try:
            country_calendar = holidays.country_holidays(country_code, years=[year])
        except (NotImplementedError, ValueError, KeyError):
            logger.debug("Holiday calendar unavailable for country %s.", country_code)
            continue
        except Exception:
            logger.exception("Could not load holiday calendar for %s.", country_code)
            continue

        for holiday_day, name in country_calendar.items():
            if isinstance(holiday_day, datetime):
                holiday_day = holiday_day.date()
            if isinstance(holiday_day, date):
                add(holiday_day, str(name))

    for (month, day_number), name in COMMON_OBSERVANCES.items():
        try:
            add(date(year, month, day_number), name)
        except ValueError:
            continue

    return {day: tuple(names) for day, names in result.items()}


def get_holidays(year: int, regions: list[str]) -> dict[date, list[str]]:
    return {
        day: list(names)
        for day, names in get_holidays_cached(year, tuple(sorted(set(regions)))).items()
    }


def get_holidays_for_month(
    year: int,
    month: int,
    regions: list[str],
) -> dict[date, list[str]]:
    result: dict[date, list[str]] = {}

    for holiday_year in (year - 1, year, year + 1):
        for day, names in get_holidays(holiday_year, regions).items():
            if day.year != year or day.month != month:
                continue
            for name in names:
                existing = result.setdefault(day, [])
                if name not in existing:
                    existing.append(name)

    return result


def build_calendar_grid(
    year: int,
    month: int,
    marked_days: dict[int, set[str]],
) -> str:
    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    lines = ["Su    Mo    Tu    We    Th    Fr    Sa"]

    for week in weeks:
        cells = []
        for day_number in week:
            if day_number == 0:
                cells.append("      ")
                continue

            markers = marked_days.get(day_number, set())
            suffix = "".join(
                marker for marker in ("B", "E", "H") if marker in markers
            )
            cells.append(f"{f'{day_number:02d} {suffix}':<6}")

        lines.append("".join(cells).rstrip())

    return "\n".join(lines)


def split_field_text(text: str, limit: int = 1000) -> list[str]:
    if not text:
        return []

    chunks = []
    current = ""

    for line in text.splitlines():
        if len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            while len(line) > limit:
                chunks.append(line[:limit])
                line = line[limit:]

        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit and current:
            chunks.append(current)
            current = line
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks


def parse_calendar_title(message: discord.Message):
    if not message.embeds:
        return None

    title = message.embeds[0].title or ""
    match = re.search(r"([A-Za-z]+)\s+(\d{4})", title)
    if not match:
        return None

    try:
        month = list(calendar.month_name).index(match.group(1))
        year = int(match.group(2))
    except (ValueError, IndexError):
        return None

    if not 1 <= month <= 12:
        return None

    return year, month


def is_test_calendar(message: discord.Message) -> bool:
    return bool(
        message.embeds
        and "TEST CALENDAR" in (message.embeds[0].title or "").upper()
    )


class AddHolidayModal(discord.ui.Modal, title="Add a Holiday"):
    holiday_name = discord.ui.TextInput(
        label="Holiday name",
        placeholder="e.g. Community Celebration",
        max_length=100,
        required=True,
    )
    holiday_date = discord.ui.TextInput(
        label="Date (YYYY-MM-DD)",
        placeholder="2026-10-31",
        max_length=10,
        required=True,
    )

    def __init__(self, view):
        super().__init__()
        self.calendar_view = view

    async def on_submit(self, interaction: discord.Interaction):
        if not await self.calendar_view.cog.check_edit_window(
            self.calendar_view.message_id,
            self.calendar_view.guild_id,
        ):
            await interaction.response.send_message(
                "This calendar's editing window has expired.",
                ephemeral=True,
            )
            return

        try:
            selected_date = date.fromisoformat(str(self.holiday_date).strip())
        except ValueError:
            await interaction.response.send_message(
                "Please enter a valid date in `YYYY-MM-DD` format.",
                ephemeral=True,
            )
            return

        if (
            selected_date.year != self.calendar_view.year
            or selected_date.month != self.calendar_view.month
        ):
            await interaction.response.send_message(
                "The date must fall within this calendar's month.",
                ephemeral=True,
            )
            return

        name = str(self.holiday_name).strip()
        if not name:
            await interaction.response.send_message(
                "Please enter a holiday name.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        await self.calendar_view.cog.save_holiday_edit(
            self.calendar_view.message_id,
            self.calendar_view.guild_id,
            selected_date,
            name,
            "add",
        )
        await self.calendar_view.cog.refresh_calendar_message(
            self.calendar_view.message_id,
            self.calendar_view.guild_id,
            self.calendar_view.year,
            self.calendar_view.month,
        )
        await interaction.followup.send(
            f"Added **{name}** on {selected_date:%b %d} to this calendar.",
            ephemeral=True,
        )


class HolidayChoiceSelect(discord.ui.Select):
    def __init__(self, view, entries, page: int):
        self.calendar_view = view
        self.entries = entries
        self.page = page

        start = page * MAX_SELECT_OPTIONS
        page_entries = entries[start:start + MAX_SELECT_OPTIONS]
        options = [
            discord.SelectOption(
                label=f"{entry['date']:%b %d} — {entry['name']}"[:100],
                value=str(index),
                description=f"Holiday on {entry['date']:%Y-%m-%d}",
            )
            for index, entry in enumerate(page_entries, start=start)
        ]

        super().__init__(
            placeholder="Choose a holiday",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        self.calendar_view.selected_entry = self.entries[int(self.values[0])]
        await interaction.response.edit_message(
            content=(
                f"Selected **{self.calendar_view.selected_entry['name']}** "
                f"on {self.calendar_view.selected_entry['date']:%b %d}. "
                f"Choose {self.calendar_view.mode}."
            ),
            view=self.calendar_view,
        )


class HolidayEditorView(discord.ui.View):
    def __init__(
        self,
        cog,
        message_id: int,
        guild_id: int,
        year: int,
        month: int,
        entries: list[dict],
        mode: str,
        page: int = 0,
    ):
        super().__init__(timeout=300)
        self.cog = cog
        self.message_id = message_id
        self.guild_id = guild_id
        self.year = year
        self.month = month
        self.entries = entries
        self.mode = mode
        self.page = page
        self.selected_entry = None

        if entries:
            self.add_item(HolidayChoiceSelect(self, entries, page))
        if page > 0:
            self.add_item(HolidayEditorPreviousButton(self))
        if (page + 1) * MAX_SELECT_OPTIONS < len(entries):
            self.add_item(HolidayEditorNextButton(self))

    async def interaction_check(self, interaction: discord.Interaction):
        return await self.cog.authorize_editor(interaction)

    async def show_page(self, interaction: discord.Interaction, page: int):
        view = HolidayEditorView(
            self.cog,
            self.message_id,
            self.guild_id,
            self.year,
            self.month,
            self.entries,
            self.mode,
            page,
        )
        await interaction.response.edit_message(
            content=f"Choose a holiday to {self.mode}.",
            view=view,
        )

    @discord.ui.button(
        label="Move",
        emoji="↪️",
        style=discord.ButtonStyle.primary,
        row=2,
    )
    async def move_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if self.mode != "move":
            return
        if not self.selected_entry:
            await interaction.response.send_message(
                "Choose a holiday first.",
                ephemeral=True,
            )
            return
        if not await self.cog.check_edit_window(self.message_id, self.guild_id):
            await interaction.response.send_message(
                "This calendar's editing window has expired.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(
            MoveHolidayModal(self, self.selected_entry)
        )

    @discord.ui.button(
        label="Remove",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def remove_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if self.mode != "remove":
            return
        if not self.selected_entry:
            await interaction.response.send_message(
                "Choose a holiday first.",
                ephemeral=True,
            )
            return
        if not await self.cog.check_edit_window(self.message_id, self.guild_id):
            await interaction.response.send_message(
                "This calendar's editing window has expired.",
                ephemeral=True,
            )
            return

        entry = self.selected_entry
        await interaction.response.defer(ephemeral=True)
        await self.cog.save_holiday_edit(
            self.message_id,
            self.guild_id,
            entry["date"],
            entry["name"],
            "remove",
        )
        await self.cog.refresh_calendar_message(
            self.message_id,
            self.guild_id,
            self.year,
            self.month,
        )
        await interaction.followup.send(
            f"Removed **{entry['name']}** from this calendar.",
            ephemeral=True,
        )


class HolidayEditorPreviousButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        self.editor = view

    async def callback(self, interaction: discord.Interaction):
        await self.editor.show_page(interaction, self.editor.page - 1)


class HolidayEditorNextButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(
            label="Next",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        self.editor = view

    async def callback(self, interaction: discord.Interaction):
        await self.editor.show_page(interaction, self.editor.page + 1)


class MoveHolidayModal(discord.ui.Modal, title="Move a Holiday"):
    new_date = discord.ui.TextInput(
        label="New date (YYYY-MM-DD)",
        placeholder="2026-10-15",
        max_length=10,
        required=True,
    )

    def __init__(self, editor, entry):
        super().__init__()
        self.editor = editor
        self.entry = entry

    async def on_submit(self, interaction: discord.Interaction):
        if not await self.editor.cog.check_edit_window(
            self.editor.message_id,
            self.editor.guild_id,
        ):
            await interaction.response.send_message(
                "This calendar's editing window has expired.",
                ephemeral=True,
            )
            return

        try:
            destination = date.fromisoformat(str(self.new_date).strip())
        except ValueError:
            await interaction.response.send_message(
                "Please enter a valid date in `YYYY-MM-DD` format.",
                ephemeral=True,
            )
            return

        if destination.year != self.editor.year or destination.month != self.editor.month:
            await interaction.response.send_message(
                "The new date must be in this calendar's month.",
                ephemeral=True,
            )
            return

        original = self.entry["date"]
        name = self.entry["name"]

        if destination == original:
            await interaction.response.send_message(
                "Choose a different date to move this holiday.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        await self.editor.cog.save_holiday_edit(
            self.editor.message_id,
            self.editor.guild_id,
            original,
            name,
            "remove",
        )
        await self.editor.cog.save_holiday_edit(
            self.editor.message_id,
            self.editor.guild_id,
            destination,
            name,
            "add",
        )
        await self.editor.cog.refresh_calendar_message(
            self.editor.message_id,
            self.editor.guild_id,
            self.editor.year,
            self.editor.month,
        )
        await interaction.followup.send(
            f"Moved **{name}** from {original:%b %d} to {destination:%b %d} "
            "on this calendar.",
            ephemeral=True,
        )


class CalendarPostView(discord.ui.View):
    def __init__(self, cog, message_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.message_id = message_id

    @discord.ui.button(
        label="Edit Calendar",
        emoji="📝",
        style=discord.ButtonStyle.secondary,
        custom_id="ratburn:monthly_calendar:edit",
    )
    async def edit_calendar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await self.cog.authorize_editor(interaction):
            return

        if interaction.message is None:
            await interaction.response.send_message(
                "I couldn't identify this calendar message.",
                ephemeral=True,
            )
            return

        if not await self.cog.check_edit_window(
            interaction.message.id,
            interaction.guild_id,
        ):
            await interaction.response.send_message(
                "This calendar's editing window has expired.",
                ephemeral=True,
            )
            return

        parsed = parse_calendar_title(interaction.message)
        if not parsed:
            await interaction.response.send_message(
                "I couldn't determine this calendar's month.",
                ephemeral=True,
            )
            return

        year, month = parsed
        entries = await self.cog.get_editable_holidays(
            interaction.message.id,
            interaction.guild_id,
            year,
            month,
        )

        view = CalendarEditMenu(
            self.cog,
            interaction.message.id,
            interaction.guild_id,
            year,
            month,
            entries,
        )
        await interaction.response.send_message(
            f"Editing **{calendar.month_name[month]} {year}**. "
            "Changes affect this post only.",
            view=view,
            ephemeral=True,
        )


class CalendarEditMenu(discord.ui.View):
    def __init__(
        self,
        cog,
        message_id: int,
        guild_id: int,
        year: int,
        month: int,
        entries: list[dict],
    ):
        super().__init__(timeout=300)
        self.cog = cog
        self.message_id = message_id
        self.guild_id = guild_id
        self.year = year
        self.month = month
        self.entries = entries

    async def interaction_check(self, interaction: discord.Interaction):
        return await self.cog.authorize_editor(interaction)

    @discord.ui.button(
        label="Add Holiday",
        emoji="➕",
        style=discord.ButtonStyle.success,
    )
    async def add_holiday(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await self.cog.check_edit_window(self.message_id, self.guild_id):
            await interaction.response.send_message(
                "This calendar's editing window has expired.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(AddHolidayModal(self))

    @discord.ui.button(
        label="Move Holiday",
        emoji="↪️",
        style=discord.ButtonStyle.primary,
    )
    async def move_holiday(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await self.cog.check_edit_window(self.message_id, self.guild_id):
            await interaction.response.send_message(
                "This calendar's editing window has expired.",
                ephemeral=True,
            )
            return
        if not self.entries:
            await interaction.response.send_message(
                "There are no holidays to move in this calendar.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Choose a holiday to move.",
            view=HolidayEditorView(
                self.cog,
                self.message_id,
                self.guild_id,
                self.year,
                self.month,
                self.entries,
                "move",
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Remove Holiday",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
    )
    async def remove_holiday(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not await self.cog.check_edit_window(self.message_id, self.guild_id):
            await interaction.response.send_message(
                "This calendar's editing window has expired.",
                ephemeral=True,
            )
            return
        if not self.entries:
            await interaction.response.send_message(
                "There are no holidays to remove from this calendar.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Choose a holiday to remove.",
            view=HolidayEditorView(
                self.cog,
                self.message_id,
                self.guild_id,
                self.year,
                self.month,
                self.entries,
                "remove",
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Finish Editing",
        emoji="✅",
        style=discord.ButtonStyle.secondary,
    )
    async def finish_editing(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.edit_message(
            content="Calendar editing finished.",
            view=None,
        )


class MonthlyCalendar(commands.Cog):
    calendar = app_commands.Group(
        name="calendar",
        description="Monthly calendar tools",
    )

    def __init__(self, bot):
        self.bot = bot
        self.calendar_loop.start()

    def cog_unload(self):
        self.calendar_loop.cancel()

    @tasks.loop(minutes=1)
    async def calendar_loop(self):
        for guild in self.bot.guilds:
            try:
                await self.check_guild(guild)
            except Exception:
                logger.exception(
                    "Unexpected error while checking monthly calendar for guild %s",
                    guild.id,
                )

    @calendar_loop.before_loop
    async def before_calendar_loop(self):
        await self.bot.wait_until_ready()
        await self.register_persistent_views()

    async def register_persistent_views(self):
        for guild in self.bot.guilds:
            config = self.bot.database.get_config(guild.id)
            message_id = config["monthly_calendar_message_id"] if config else None
            if message_id:
                self.bot.add_view(
                    CalendarPostView(self, message_id),
                    message_id=message_id,
                )

    async def authorize_editor(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This action can only be used in a server.",
                ephemeral=True,
            )
            return False

        if interaction.user.guild_permissions.administrator:
            return True

        config = self.bot.database.get_config(interaction.guild.id)
        staff_role_id = config["staff_role_id"] if config else None

        if staff_role_id:
            member = interaction.guild.get_member(interaction.user.id)
            if member and any(role.id == staff_role_id for role in member.roles):
                return True

        await interaction.response.send_message(
            "Only server administrators or members with the configured Staff Role "
            "can edit this calendar.",
            ephemeral=True,
        )
        return False

    async def check_edit_window(self, message_id: int, guild_id: int | None) -> bool:
        if guild_id is None:
            return False

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return False

        config = self.bot.database.get_config(guild_id)
        channel_id = (
            config["monthly_calendar_channel_id"] or config["event_channel_id"]
        ) if config else None
        if not channel_id:
            return False

        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return False

        if not isinstance(channel, discord.TextChannel):
            return False

        try:
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return False

        return datetime.now(timezone.utc) - message.created_at <= EDIT_WINDOW

    @calendar.command(
        name="test",
        description="Post a test version of this month's calendar",
    )
    async def test_calendar(self, interaction: discord.Interaction):
        if not await self.authorize_editor(interaction):
            return

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        config = self.bot.database.get_config(interaction.guild.id)
        if not config:
            await interaction.response.send_message(
                "Configure Ratburn before testing the calendar.",
                ephemeral=True,
            )
            return

        timezone_name = config["timezone"]
        if not timezone_name:
            await interaction.response.send_message(
                "Configure the server timezone before testing the calendar.",
                ephemeral=True,
            )
            return

        try:
            tz = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            await interaction.response.send_message(
                "The configured timezone is invalid. Please update it first.",
                ephemeral=True,
            )
            return

        channel_id = (
            config["monthly_calendar_channel_id"] or config["event_channel_id"]
        )
        if not channel_id:
            await interaction.response.send_message(
                "Configure a Monthly Calendar Channel or Event Channel first.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                channel = None

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "I couldn't access the configured calendar channel.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        now = datetime.now(tz)
        embed = await self.build_monthly_calendar(
            interaction.guild,
            tz,
            now.year,
            now.month,
            test_mode=True,
        )

        try:
            message = await channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            logger.exception(
                "Failed to post test calendar for guild %s.",
                interaction.guild.id,
            )
            await interaction.followup.send(
                "I couldn't post the test calendar. Check my channel permissions.",
                ephemeral=True,
            )
            return

        try:
            await message.edit(
                view=CalendarPostView(self, message.id),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            logger.exception(
                "Could not attach the edit button to test calendar %s.",
                message.id,
            )

        await interaction.followup.send(
            f"Test calendar posted in {channel.mention}. "
            "The normal monthly posting tracker was not changed.",
            ephemeral=True,
        )

    async def check_guild(self, guild: discord.Guild):
        config = self.bot.database.get_config(guild.id)
        if not config or not config["monthly_calendar_enabled"]:
            return

        timezone_name = config["timezone"]
        if not timezone_name:
            return

        try:
            tz = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            logger.error(
                "Invalid timezone for monthly calendar in guild %s: %s",
                guild.id,
                timezone_name,
            )
            return

        now = datetime.now(tz)
        if now.day != 1 or now.timetz().replace(tzinfo=None) < POST_TIME:
            return

        month_key = now.strftime("%Y-%m")
        if config["monthly_calendar_last_posted"] == month_key:
            return

        channel_id = (
            config["monthly_calendar_channel_id"] or config["event_channel_id"]
        )
        if not channel_id:
            logger.warning(
                "Calendar enabled but no calendar or event channel is configured "
                "for guild %s.",
                guild.id,
            )
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                logger.warning(
                    "Could not access monthly calendar channel %s for guild %s.",
                    channel_id,
                    guild.id,
                )
                return

        if not isinstance(channel, discord.TextChannel):
            return

        embed = await self.build_monthly_calendar(
            guild,
            tz,
            now.year,
            now.month,
        )

        try:
            message = await channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            logger.exception(
                "Failed to post monthly calendar in guild %s.",
                guild.id,
            )
            return

        self.bot.database.set_config(
            guild.id,
            "monthly_calendar_last_posted",
            month_key,
        )
        self.bot.database.set_config(
            guild.id,
            "monthly_calendar_message_id",
            message.id,
        )
        self.bot.database.set_config(
            guild.id,
            "monthly_calendar_guild_id",
            guild.id,
        )

        try:
            await message.edit(
                view=CalendarPostView(self, message.id),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            logger.exception(
                "Could not attach the edit button to calendar %s.",
                message.id,
            )

        logger.info(
            "Posted monthly calendar for %s in guild %s.",
            month_key,
            guild.id,
        )

    async def get_base_holidays(
        self,
        guild_id: int,
        year: int,
        month: int,
    ) -> dict[date, list[str]]:
        config = self.bot.database.get_config(guild_id)
        regions = parse_regions(
            config["monthly_calendar_holiday_regions"] if config else None
        )
        return get_holidays_for_month(year, month, regions)

    async def get_editable_holidays(
        self,
        message_id: int,
        guild_id: int,
        year: int,
        month: int,
    ) -> list[dict]:
        base = await self.get_base_holidays(guild_id, year, month)
        entries = [
            {"date": day, "name": name}
            for day, names in base.items()
            for name in names
        ]

        rows = self.bot.database.connection.execute(
            """
            SELECT holiday_date, holiday_name, action
            FROM monthly_calendar_edits
            WHERE message_id = ? AND guild_id = ?
            ORDER BY holiday_date, holiday_name
            """,
            (message_id, guild_id),
        ).fetchall()

        for row in rows:
            try:
                day = date.fromisoformat(row["holiday_date"])
            except (TypeError, ValueError):
                continue

            name = row["holiday_name"]
            action = row["action"]
            if day.year != year or day.month != month:
                continue

            entries = [
                entry for entry in entries
                if not (entry["date"] == day and entry["name"] == name)
            ]
            if action == "add":
                entries.append({"date": day, "name": name})

        unique = {}
        for entry in entries:
            unique[(entry["date"], entry["name"])] = entry

        return sorted(
            unique.values(),
            key=lambda entry: (entry["date"], entry["name"].casefold()),
        )

    async def save_holiday_edit(
        self,
        message_id: int,
        guild_id: int,
        holiday_date: date,
        holiday_name: str,
        action: str,
    ):
        if action not in {"add", "move", "remove"}:
            raise ValueError("Invalid calendar holiday edit action.")

        connection = self.bot.database.connection
        connection.execute(
            """
            DELETE FROM monthly_calendar_edits
            WHERE message_id = ?
              AND guild_id = ?
              AND holiday_date = ?
              AND holiday_name = ?
            """,
            (
                message_id,
                guild_id,
                holiday_date.isoformat(),
                holiday_name,
            ),
        )
        connection.execute(
            """
            INSERT INTO monthly_calendar_edits (
                message_id,
                guild_id,
                holiday_date,
                holiday_name,
                action
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message_id,
                guild_id,
                holiday_date.isoformat(),
                holiday_name,
                action,
            ),
        )
        connection.commit()

    async def refresh_calendar_message(
        self,
        message_id: int,
        guild_id: int,
        year: int,
        month: int,
    ):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return

        config = self.bot.database.get_config(guild_id)
        tz_name = config["timezone"] if config else None
        try:
            tz = ZoneInfo(tz_name or "UTC")
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")

        channel_id = (
            config["monthly_calendar_channel_id"] or config["event_channel_id"]
        ) if config else None
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return

        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        embed = await self.build_monthly_calendar(
            guild,
            tz,
            year,
            month,
            message_id=message_id,
            test_mode=is_test_calendar(message),
        )

        try:
            await message.edit(
                embed=embed,
                view=CalendarPostView(self, message_id),
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except (discord.Forbidden, discord.HTTPException):
            logger.exception("Could not refresh calendar message %s.", message_id)

    async def build_monthly_calendar(
        self,
        guild: discord.Guild,
        tz: ZoneInfo,
        year: int,
        month: int,
        message_id: int | None = None,
        test_mode: bool = False,
    ) -> discord.Embed:
        month_name = calendar.month_name[month]
        days_in_month = calendar.monthrange(year, month)[1]
        marked_days: dict[int, set[str]] = {}
        details_by_day: dict[int, list[str]] = {}

        def mark(day_number: int, marker: str):
            marked_days.setdefault(day_number, set()).add(marker)

        def add_detail(day_number: int, text: str):
            details_by_day.setdefault(day_number, []).append(text)

        birthdays = self.bot.database.get_birthdays_for_month(guild.id, month)
        for birthday in birthdays:
            day_number = birthday["birthday_day"]
            if not 1 <= day_number <= days_in_month:
                continue

            user_id = birthday["user_id"]
            member = guild.get_member(user_id)
            if member is not None:
                display_name = member.display_name
            elif birthday["nickname"]:
                display_name = birthday["nickname"]
            else:
                display_name = f"Member {user_id}"

            mark(day_number, "B")
            add_detail(day_number, f"🎂 {display_name}")

        for event in guild.scheduled_events:
            if event.status.name.lower() in {"cancelled", "completed"}:
                continue
            if event.start_time is None:
                continue

            event_start = event.start_time.astimezone(tz)
            if event_start.year != year or event_start.month != month:
                continue

            mark(event_start.day, "E")
            event_time = event_start.strftime("%I:%M %p").lstrip("0")
            add_detail(event_start.day, f"📌 {event.name} — {event_time}")

        holidays_by_day = await self.get_base_holidays(guild.id, year, month)
        if message_id is not None:
            rows = self.bot.database.connection.execute(
                """
                SELECT holiday_date, holiday_name, action
                FROM monthly_calendar_edits
                WHERE message_id = ? AND guild_id = ?
                """,
                (message_id, guild.id),
            ).fetchall()

            for row in rows:
                try:
                    holiday_day = date.fromisoformat(row["holiday_date"])
                except (TypeError, ValueError):
                    continue
                if holiday_day.year != year or holiday_day.month != month:
                    continue

                name = row["holiday_name"]
                action = row["action"]
                if action in {"remove", "move"}:
                    holidays_by_day[holiday_day] = [
                        existing
                        for existing in holidays_by_day.get(holiday_day, [])
                        if existing != name
                    ]
                if action == "add":
                    names = holidays_by_day.setdefault(holiday_day, [])
                    if name not in names:
                        names.append(name)

        for holiday_day, names in holidays_by_day.items():
            for holiday_name in names:
                mark(holiday_day.day, "H")
                add_detail(holiday_day.day, f"🎉 {holiday_name}")

        grid = build_calendar_grid(year, month, marked_days)
        embed = discord.Embed(
            title=(
                f"🧪 TEST CALENDAR — {month_name} {year}"
                if test_mode
                else f"🗓️ {month_name} {year}"
            ),
            description=(
                f"```text\n{grid}\n```\n"
                "`B` Birthday · `E` Event · `H` Holiday\n"
                f"Timezone: `{tz.key}`"
            ),
            color=discord.Color.from_rgb(92, 128, 92),
        )

        if not details_by_day:
            embed.add_field(
                name="Dates to Note",
                value="No birthdays, scheduled events, or listed holidays this month.",
                inline=False,
            )
        else:
            detail_lines = []
            for day_number in sorted(details_by_day):
                day_date = date(year, month, day_number)
                heading = day_date.strftime("%a, %b %d").replace(" 0", " ")
                detail_lines.append(f"**{heading}**")
                detail_lines.extend(details_by_day[day_number])
                detail_lines.append("")

            chunks = split_field_text("\n".join(detail_lines).strip())
            for index, chunk in enumerate(chunks[:4], start=1):
                field_name = (
                    "Dates to Note"
                    if index == 1
                    else f"Dates to Note (continued {index})"
                )
                embed.add_field(name=field_name, value=chunk, inline=False)

            if len(chunks) > 4:
                embed.add_field(
                    name="More dates",
                    value="Additional entries were omitted to stay within Discord's embed limits.",
                    inline=False,
                )

        embed.set_footer(
            text=(
                "TEST CALENDAR • Posted by Mr Ratburn • No notifications sent"
                if test_mode
                else "Posted by Mr Ratburn • No notifications sent"
            )
        )
        return embed


async def setup(bot):
    await bot.add_cog(MonthlyCalendar(bot))
