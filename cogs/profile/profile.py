import calendar
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import commands


TIMEZONE_OPTIONS = [
    ("UTC-12:00", "International Date Line West", "Etc/GMT+12"),
    ("UTC-11:00", "Samoa, Midway Islands", "Pacific/Pago_Pago"),
    ("UTC-10:00", "Hawaii, Cook Islands", "Pacific/Honolulu"),
    ("UTC-09:00", "Alaska", "America/Anchorage"),
    ("UTC-08:00", "Pacific Standard Time (US & Canada)", "America/Los_Angeles"),
    ("UTC-07:00", "Mountain Standard Time (US & Canada)", "America/Denver"),
    ("UTC-06:00", "Central Standard Time (US & Canada), Central America", "America/Chicago"),
    ("UTC-05:00", "Eastern Standard Time (US & Canada), Colombia, Peru", "America/New_York"),
    ("UTC-04:00", "Atlantic Standard Time, Bolivia, Chile (Standard)", "America/Halifax"),
    ("UTC-03:00", "Argentina, Brazil (East), Greenland", "America/Argentina/Buenos_Aires"),
    ("UTC-02:00", "South Georgia & the South Sandwich Islands", "Atlantic/South_Georgia"),
    ("UTC-01:00", "Azores, Cabo Verde", "Atlantic/Azores"),
    ("UTC±00:00", "Greenwich Mean Time (GMT), Western Europe, UK", "Europe/London"),
    ("UTC+01:00", "Central European Time, West Africa", "Europe/Berlin"),
    ("UTC+02:00", "Eastern European Time, Central Africa", "Europe/Bucharest"),
    ("UTC+03:00", "Moscow Standard Time, East Africa, Arabia", "Europe/Moscow"),
    ("UTC+04:00", "Gulf Standard Time, Mauritius", "Asia/Dubai"),
    ("UTC+05:00", "Pakistan Standard Time, Uzbekistan", "Asia/Karachi"),
    ("UTC+06:00", "Bangladesh Standard Time, Kazakhstan (East)", "Asia/Dhaka"),
    ("UTC+07:00", "Indochina Time, Western Indonesia", "Asia/Bangkok"),
    ("UTC+08:00", "China Standard Time, Western Australia, Singapore", "Asia/Shanghai"),
    ("UTC+09:00", "Japan Standard Time, Korea Standard Time", "Asia/Tokyo"),
    ("UTC+10:00", "Australian Eastern Standard Time, Papua New Guinea", "Australia/Sydney"),
    ("UTC+11:00", "Solomon Islands, Vanuatu", "Pacific/Guadalcanal"),
    ("UTC+12:00", "Fiji, New Zealand (Standard)", "Pacific/Auckland"),
]


PRONOUN_OPTIONS = {
    "she/her": [
        {"subject": "she", "object": "her"},
    ],
    "he/him": [
        {"subject": "he", "object": "him"},
    ],
    "they/them": [
        {"subject": "they", "object": "them"},
    ],
    "she/they": [
        {"subject": "she", "object": "her"},
        {"subject": "they", "object": "them"},
    ],
    "he/they": [
        {"subject": "he", "object": "him"},
        {"subject": "they", "object": "them"},
    ],
    "they/she": [
        {"subject": "they", "object": "them"},
        {"subject": "she", "object": "her"},
    ],
    "they/he": [
        {"subject": "they", "object": "them"},
        {"subject": "he", "object": "him"},
    ],
    "any pronouns": [
        {"subject": "she", "object": "her"},
        {"subject": "he", "object": "him"},
        {"subject": "they", "object": "them"},
    ],
    "ask me": None,
    "prefer not to say": [
        {"subject": "they", "object": "them"},
    ],
}


def build_profile_embed(
    member: discord.Member,
    profile
):
    embed = discord.Embed(
        title="🐀 Your Ratburn Profile",
        description=(
            f"Here's what Ratburn has on file for {member.mention}."
        )
    )

    if profile["birthday_month"] and profile["birthday_day"]:
        birthday = (
            f"{calendar.month_name[profile['birthday_month']]} "
            f"{profile['birthday_day']}"
        )

        if profile["birthday_year"]:
            birthday += f", {profile['birthday_year']}"
    else:
        birthday = "Not provided"

    nickname = profile["nickname"] or member.display_name

    pronouns = "they/them"

    if profile["pronouns"]:
        try:
            pronoun_sets = json.loads(profile["pronouns"])

            if pronoun_sets:
                pronouns = " • ".join(
                    f"{item['subject']}/{item['object']}"
                    for item in pronoun_sets
                )
        except (json.JSONDecodeError, TypeError):
            pronouns = profile["pronouns"]

    timezone_name = profile["timezone"] or "Not provided"

    if profile["rules_acknowledged"]:
        rules = "✅ Acknowledged"
    else:
        rules = "❌ Not acknowledged"

    embed.add_field(
        name="🎂 Birthday",
        value=birthday,
        inline=True
    )

    embed.add_field(
        name="🏷️ Nickname",
        value=nickname,
        inline=True
    )

    embed.add_field(
        name="💬 Pronouns",
        value=pronouns,
        inline=True
    )

    embed.add_field(
        name="🌎 Timezone",
        value=timezone_name,
        inline=True
    )

    embed.add_field(
        name="📜 Rules",
        value=rules,
        inline=True
    )

    embed.add_field(
        name="🧠 Daily Quiz",
        value=f"**{profile['quiz_points']}** points",
        inline=True
    )

    embed.set_footer(
        text="Ratburn's got you on file. 🐀"
    )

    return embed


def get_pronoun_display(pronouns):
    if not pronouns:
        return "they/them"

    try:
        pronoun_sets = json.loads(pronouns)

        if pronoun_sets:
            return " • ".join(
                f"{item['subject']}/{item['object']}"
                for item in pronoun_sets
            )
    except (json.JSONDecodeError, TypeError):
        pass

    return pronouns


def get_birthday_display(
    month,
    day,
    year
):
    if not month or not day:
        return "Not provided"

    birthday = (
        f"{calendar.month_name[month]} "
        f"{day}"
    )

    if year:
        birthday += f", {year}"

    return birthday


def parse_timestamp(timestamp):
    if not timestamp:
        return None

    try:
        return datetime.fromisoformat(timestamp)
    except ValueError:
        return None


class BirthdayEditModal(
    discord.ui.Modal,
    title="Edit Birthday"
):
    month = discord.ui.TextInput(
        label="Birth month",
        placeholder="Example: 7",
        min_length=1,
        max_length=2,
        required=True
    )

    day = discord.ui.TextInput(
        label="Birth day",
        placeholder="Example: 15",
        min_length=1,
        max_length=2,
        required=True
    )

    year = discord.ui.TextInput(
        label="Birth year",
        placeholder="Example: 1994 (optional)",
        min_length=4,
        max_length=4,
        required=False
    )

    def __init__(self, edit_view):
        super().__init__()

        self.edit_view = edit_view

        if edit_view.birthday_month is not None:
            self.month.default = str(edit_view.birthday_month)

        if edit_view.birthday_day is not None:
            self.day.default = str(edit_view.birthday_day)

        if edit_view.birthday_year is not None:
            self.year.default = str(edit_view.birthday_year)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        try:
            month = int(self.month.value)
            day = int(self.day.value)
        except ValueError:
            await interaction.response.send_message(
                "Please enter numbers for the month and day.",
                ephemeral=True
            )
            return

        if month < 1 or month > 12:
            await interaction.response.send_message(
                "Please enter a month from 1 to 12.",
                ephemeral=True
            )
            return

        try:
            max_day = calendar.monthrange(
                2000,
                month
            )[1]
        except ValueError:
            await interaction.response.send_message(
                "That month isn't valid.",
                ephemeral=True
            )
            return

        if day < 1 or day > max_day:
            await interaction.response.send_message(
                f"{calendar.month_name[month]} doesn't have "
                f"{day} days.",
                ephemeral=True
            )
            return

        year = None

        if self.year.value.strip():
            try:
                year = int(self.year.value)
            except ValueError:
                await interaction.response.send_message(
                    "Please enter a four-digit year.",
                    ephemeral=True
                )
                return

            if year < 1900 or year > 2100:
                await interaction.response.send_message(
                    "Please enter a valid year.",
                    ephemeral=True
                )
                return

        self.edit_view.birthday_month = month
        self.edit_view.birthday_day = day
        self.edit_view.birthday_year = year

        await self.edit_view.refresh(interaction)


class NicknameEditModal(
    discord.ui.Modal,
    title="Edit Nickname"
):
    nickname = discord.ui.TextInput(
        label="Nickname",
        placeholder="What should Ratburn call you?",
        min_length=1,
        max_length=32,
        required=True
    )

    def __init__(self, edit_view):
        super().__init__()

        self.edit_view = edit_view

        if edit_view.nickname:
            self.nickname.default = edit_view.nickname

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        nickname = self.nickname.value.strip()

        if not nickname:
            await interaction.response.send_message(
                "Please enter a nickname.",
                ephemeral=True
            )
            return

        self.edit_view.nickname = nickname

        await self.edit_view.refresh(interaction)


class PronounSelect(discord.ui.Select):
    def __init__(self, edit_view):
        options = [
            discord.SelectOption(
                label="She / Her",
                value="she/her"
            ),
            discord.SelectOption(
                label="He / Him",
                value="he/him"
            ),
            discord.SelectOption(
                label="They / Them",
                value="they/them"
            ),
            discord.SelectOption(
                label="She / They",
                value="she/they"
            ),
            discord.SelectOption(
                label="He / They",
                value="he/they"
            ),
            discord.SelectOption(
                label="They / She",
                value="they/she"
            ),
            discord.SelectOption(
                label="They / He",
                value="they/he"
            ),
            discord.SelectOption(
                label="Any Pronouns",
                value="any pronouns"
            ),
            discord.SelectOption(
                label="Ask Me",
                value="ask me"
            ),
            discord.SelectOption(
                label="Prefer Not to Say",
                value="prefer not to say"
            ),
        ]

        current = get_pronoun_display(
            edit_view.pronouns
        )

        for option in options:
            if option.value == current:
                option.default = True

        super().__init__(
            placeholder="Choose your pronouns...",
            options=options,
            row=0
        )

        self.edit_view = edit_view

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        selected = self.values[0]

        if selected == "ask me":
            self.edit_view.pronouns = json.dumps(
                PRONOUN_OPTIONS["they/them"]
            )
        else:
            self.edit_view.pronouns = json.dumps(
                PRONOUN_OPTIONS[selected]
            )

        await self.edit_view.refresh(interaction)


class TimezoneSelect(discord.ui.Select):
    def __init__(self, edit_view):
        options = [
            discord.SelectOption(
                label=offset,
                description=name[:100],
                value=iana
            )
            for offset, name, iana in TIMEZONE_OPTIONS
        ]

        for option in options:
            if option.value == edit_view.timezone:
                option.default = True

        super().__init__(
            placeholder="Choose your timezone...",
            options=options,
            row=1
        )

        self.edit_view = edit_view

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.edit_view.timezone = self.values[0]

        await self.edit_view.refresh(interaction)


class ProfileEditView(discord.ui.View):
    def __init__(
        self,
        bot,
        member: discord.Member,
        original_profile
    ):
        super().__init__(timeout=600)

        self.bot = bot
        self.member = member
        self.original_profile = original_profile

        self.birthday_month = original_profile["birthday_month"]
        self.birthday_day = original_profile["birthday_day"]
        self.birthday_year = original_profile["birthday_year"]

        self.nickname = original_profile["nickname"]
        self.pronouns = original_profile["pronouns"]
        self.timezone = original_profile["timezone"]

        self.add_item(
            PronounSelect(self)
        )

        self.add_item(
            TimezoneSelect(self)
        )

        self.birthday_button = discord.ui.Button(
            label="Edit Birthday",
            emoji="🎂",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        self.birthday_button.callback = self.edit_birthday
        self.add_item(self.birthday_button)

        self.nickname_button = discord.ui.Button(
            label="Edit Nickname",
            emoji="🏷️",
            style=discord.ButtonStyle.secondary,
            row=2
        )
        self.nickname_button.callback = self.edit_nickname
        self.add_item(self.nickname_button)

        self.save_button = discord.ui.Button(
            label="Save Profile",
            emoji="💾",
            style=discord.ButtonStyle.success,
            row=3
        )
        self.save_button.callback = self.save_profile
        self.add_item(self.save_button)

        self.cancel_button = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            row=3
        )
        self.cancel_button.callback = self.cancel
        self.add_item(self.cancel_button)

    async def check_user(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This isn't your profile!",
                ephemeral=True
            )
            return False

        return True

    def has_changes(self):
        return any([
            self.birthday_month != self.original_profile["birthday_month"],
            self.birthday_day != self.original_profile["birthday_day"],
            self.birthday_year != self.original_profile["birthday_year"],
            self.nickname != self.original_profile["nickname"],
            self.pronouns != self.original_profile["pronouns"],
            self.timezone != self.original_profile["timezone"],
        ])

    def build_edit_embed(self):
        embed = discord.Embed(
            title="✏️ Edit Your Ratburn Profile",
            description=(
                "Make any changes you'd like, then hit **Save Profile**.\n\n"
                "Your weekly profile edit is only used when you save "
                "an actual change."
            )
        )

        embed.add_field(
            name="🎂 Birthday",
            value=get_birthday_display(
                self.birthday_month,
                self.birthday_day,
                self.birthday_year
            ),
            inline=True
        )

        embed.add_field(
            name="🏷️ Nickname",
            value=self.nickname or self.member.display_name,
            inline=True
        )

        embed.add_field(
            name="💬 Pronouns",
            value=get_pronoun_display(
                self.pronouns
            ),
            inline=True
        )

        embed.add_field(
            name="🌎 Timezone",
            value=self.timezone or "Not provided",
            inline=True
        )

        return embed

    async def refresh(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.edit_message(
            embed=self.build_edit_embed(),
            view=self
        )

    async def edit_birthday(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await interaction.response.send_modal(
            BirthdayEditModal(self)
        )

    async def edit_nickname(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await interaction.response.send_modal(
            NicknameEditModal(self)
        )

    async def save_profile(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        if not self.has_changes():
            await interaction.response.send_message(
                "Nothing has changed, so your weekly profile edit "
                "wasn't used.",
                ephemeral=True
            )
            return

        last_edited = parse_timestamp(
            self.bot.database.get_profile_last_edited(
                self.member.guild.id,
                self.member.id
            )
        )

        now = datetime.now(timezone.utc)

        if last_edited is not None:
            if last_edited.tzinfo is None:
                last_edited = last_edited.replace(
                    tzinfo=timezone.utc
                )

            cooldown_ends = last_edited + timedelta(days=7)

            if now < cooldown_ends:
                remaining = cooldown_ends - now
                days = remaining.days
                hours = remaining.seconds // 3600

                if days > 0:
                    message = (
                        f"You've already edited your profile this week. "
                        f"You can save another edit in **{days} day"
                        f"{'s' if days != 1 else ''}**."
                    )
                else:
                    message = (
                        f"You've already edited your profile this week. "
                        f"You can save another edit in about "
                        f"**{hours} hour"
                        f"{'s' if hours != 1 else ''}**."
                    )

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )
                return

        await interaction.response.defer()

        guild_id = self.member.guild.id
        user_id = self.member.id

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "birthday_month",
            self.birthday_month
        )

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "birthday_day",
            self.birthday_day
        )

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "birthday_year",
            self.birthday_year
        )

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "nickname",
            self.nickname
        )

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "pronouns",
            self.pronouns
        )

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "timezone",
            self.timezone
        )

        self.bot.database.set_profile_last_edited(
            guild_id,
            user_id,
            now.isoformat()
        )

        if self.nickname:
            try:
                await self.member.edit(
                    nick=self.nickname,
                    reason="Ratburn profile edit"
                )
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

        profile = self.bot.database.get_member_profile(
            guild_id,
            user_id
        )

        embed = build_profile_embed(
            self.member,
            profile
        )

        await interaction.edit_original_response(
            embed=embed,
            view=None
        )

        self.stop()

    async def cancel(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        profile = self.bot.database.get_member_profile(
            self.member.guild.id,
            self.member.id
        )

        await interaction.response.edit_message(
            embed=build_profile_embed(
                self.member,
                profile
            ),
            view=None
        )

        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="profile",
        description="View your Ratburn profile."
    )
    async def profile(
        self,
        interaction: discord.Interaction
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return

        profile = self.bot.database.get_member_profile(
            interaction.guild.id,
            interaction.user.id
        )

        embed = build_profile_embed(
            interaction.user,
            profile
        )

        view = ProfileView(
            self.bot,
            interaction.user,
            profile
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )


class ProfileView(discord.ui.View):
    def __init__(
        self,
        bot,
        member: discord.Member,
        profile
    ):
        super().__init__(timeout=600)

        self.bot = bot
        self.member = member
        self.profile = profile

        self.edit_button = discord.ui.Button(
            label="Edit Profile",
            emoji="✏️",
            style=discord.ButtonStyle.secondary
        )
        self.edit_button.callback = self.edit_profile
        self.add_item(self.edit_button)

    async def edit_profile(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This isn't your profile!",
                ephemeral=True
            )
            return

        last_edited = parse_timestamp(
            self.bot.database.get_profile_last_edited(
                self.member.guild.id,
                self.member.id
            )
        )

        if last_edited is not None:
            if last_edited.tzinfo is None:
                last_edited = last_edited.replace(
                    tzinfo=timezone.utc
                )

            cooldown_ends = (
                last_edited + timedelta(days=7)
            )

            now = datetime.now(timezone.utc)

            if now < cooldown_ends:
                remaining = cooldown_ends - now
                days = remaining.days
                hours = remaining.seconds // 3600

                if days > 0:
                    message = (
                        f"You've already edited your profile this week. "
                        f"You can edit it again in **{days} day"
                        f"{'s' if days != 1 else ''}**."
                    )
                else:
                    message = (
                        f"You've already edited your profile this week. "
                        f"You can edit it again in about **{hours} hour"
                        f"{'s' if hours != 1 else ''}**."
                    )

                await interaction.response.send_message(
                    message,
                    ephemeral=True
                )
                return

        profile = self.bot.database.get_member_profile(
            self.member.guild.id,
            self.member.id
        )

        view = ProfileEditView(
            self.bot,
            self.member,
            profile
        )

        await interaction.response.edit_message(
            embed=view.build_edit_embed(),
            view=view
        )


async def setup(bot):
    await bot.add_cog(Profile(bot))
