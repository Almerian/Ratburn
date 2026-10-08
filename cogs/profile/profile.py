import calendar
import json
from datetime import datetime, timedelta, timezone

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
    profile,
    demerit_count: int,
    own_profile: bool = True
):
    embed = discord.Embed(
        title=(
            "🐀 Your Ratburn Profile"
            if own_profile
            else f"🐀 {member.display_name}'s Ratburn Profile"
        ),
        description=(
            f"Here's what Ratburn has on file for "
            f"{member.mention}."
        ),
        color=discord.Color.from_rgb(139, 69, 19)
    )

    birthday = "Not set"

    if profile["birthday_month"] and profile["birthday_day"]:
        month_name = calendar.month_name[
            profile["birthday_month"]
        ]

        birthday = (
            f"{month_name} "
            f"{profile['birthday_day']}"
        )

        if own_profile and profile["birthday_year"]:
            birthday += f", {profile['birthday_year']}"

    embed.add_field(
        name="🎂 Birthday",
        value=birthday,
        inline=True
    )

    nickname = profile["nickname"] or "Not set"

    embed.add_field(
        name="🏷️ Nickname",
        value=nickname,
        inline=True
    )

    pronouns = get_pronoun_display(profile)

    embed.add_field(
        name="🗣️ Pronouns",
        value=pronouns,
        inline=True
    )

    timezone_name = profile["timezone"] or "Not set"

    embed.add_field(
        name="🌎 Timezone",
        value=timezone_name,
        inline=True
    )

    embed.add_field(
        name="🧠 Daily Quiz Points",
        value=str(profile["quiz_points"]),
        inline=True
    )

    embed.add_field(
        name="📋 Demerits",
        value=str(demerit_count),
        inline=True
    )

    rules_status = (
        "Acknowledged"
        if profile["rules_acknowledged"]
        else "Not acknowledged"
    )

    embed.add_field(
        name="📜 Rules",
        value=rules_status,
        inline=True
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.set_footer(
        text="Ratburn's got you on file. 🐀"
    )

    return embed


def get_pronoun_display(profile):
    pronoun_index = profile["pronoun_index"]

    if pronoun_index is None:
        return "Not set"

    try:
        pronoun_index = int(pronoun_index)
    except (TypeError, ValueError):
        return "Not set"

    if pronoun_index < 0 or pronoun_index >= len(PRONOUN_OPTIONS):
        return "Not set"

    label, value = PRONOUN_OPTIONS[pronoun_index]

    if value == "custom":
        custom_pronouns = profile["pronouns"]

        if custom_pronouns:
            return custom_pronouns

        return "Custom"

    return label


def get_pronoun_value(profile):
    pronoun_index = profile["pronoun_index"]

    if pronoun_index is None:
        return None

    try:
        pronoun_index = int(pronoun_index)
    except (TypeError, ValueError):
        return None

    if pronoun_index < 0 or pronoun_index >= len(PRONOUN_OPTIONS):
        return None

    return PRONOUN_OPTIONS[pronoun_index][1]


def get_birthday_display(profile):
    if not profile["birthday_month"] or not profile["birthday_day"]:
        return "Not set"

    month_name = calendar.month_name[
        profile["birthday_month"]
    ]

    birthday = (
        f"{month_name} "
        f"{profile['birthday_day']}"
    )

    if profile["birthday_year"]:
        birthday += f", {profile['birthday_year']}"

    return birthday


def parse_timestamp(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


class BirthdayEditModal(discord.ui.Modal):
    def __init__(self, profile_view):
        super().__init__(
            title="Edit Birthday"
        )

        self.profile_view = profile_view

        self.birthday = discord.ui.TextInput(
            label="Birthday",
            placeholder="MM/DD/YYYY",
            required=False,
            max_length=10
        )

        self.add_item(self.birthday)

        current = get_birthday_display(
            profile_view.original_profile
        )

        if current != "Not set":
            self.birthday.default = current

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        value = self.birthday.value.strip()

        if not value:
            self.profile_view.birthday_month = None
            self.profile_view.birthday_day = None
            self.profile_view.birthday_year = None

            await interaction.response.send_message(
                "Birthday cleared.",
                ephemeral=True
            )
            return

        try:
            parsed = datetime.strptime(
                value,
                "%m/%d/%Y"
            )
        except ValueError:
            await interaction.response.send_message(
                "Please enter your birthday as MM/DD/YYYY.",
                ephemeral=True
            )
            return

        self.profile_view.birthday_month = parsed.month
        self.profile_view.birthday_day = parsed.day
        self.profile_view.birthday_year = parsed.year

        await interaction.response.send_message(
            "Birthday updated.",
            ephemeral=True
        )


class NicknameEditModal(discord.ui.Modal):
    def __init__(self, profile_view):
        super().__init__(
            title="Edit Nickname"
        )

        self.profile_view = profile_view

        self.nickname = discord.ui.TextInput(
            label="Nickname",
            placeholder="What should Ratburn call you?",
            required=False,
            max_length=32
        )

        current = profile_view.original_profile["nickname"]

        if current:
            self.nickname.default = current

        self.add_item(self.nickname)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        self.profile_view.nickname = (
            self.nickname.value.strip()
            or None
        )

        await interaction.response.send_message(
            "Nickname updated.",
            ephemeral=True
        )


class PronounSelect(discord.ui.Select):
    def __init__(self, profile_view):
        options = [
            discord.SelectOption(
                label=label,
                value=value
            )
            for label, value in PRONOUN_OPTIONS
        ]

        super().__init__(
            placeholder="Choose your pronouns...",
            options=options
        )

        self.profile_view = profile_view

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        selected = self.values[0]

        for index, (_, value) in enumerate(PRONOUN_OPTIONS):
            if value == selected:
                self.profile_view.pronoun_index = index
                break

        if selected != "custom":
            self.profile_view.pronouns = None

            await interaction.response.send_message(
                "Pronouns updated.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            CustomPronounModal(
                self.profile_view
            )
        )


class CustomPronounModal(discord.ui.Modal):
    def __init__(self, profile_view):
        super().__init__(
            title="Custom Pronouns"
        )

        self.profile_view = profile_view

        self.pronouns = discord.ui.TextInput(
            label="Pronouns",
            placeholder="e.g. ze/zir",
            required=True,
            max_length=32
        )

        self.add_item(self.pronouns)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        self.profile_view.pronouns = (
            self.pronouns.value.strip()
        )

        await interaction.response.send_message(
            "Custom pronouns updated.",
            ephemeral=True
        )


class TimezoneSelect(discord.ui.Select):
    def __init__(self, profile_view):
        options = [
            discord.SelectOption(
                label=label,
                value=iana,
                description=description,
                default=(
                    profile_view.original_profile["timezone"]
                    == iana
                )
            )
            for label, iana, description in TIMEZONE_OPTIONS
        ]

        super().__init__(
            placeholder="Choose your timezone...",
            options=options
        )

        self.profile_view = profile_view

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.profile_view.timezone = self.values[0]

        await interaction.response.send_message(
            "Timezone updated.",
            ephemeral=True
        )


class RulesAcknowledgementButton(discord.ui.Button):
    def __init__(self, profile_view):
        super().__init__(
            label="I Acknowledge the Rules",
            style=discord.ButtonStyle.success
        )

        self.profile_view = profile_view

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.profile_view.rules_acknowledged = True

        await interaction.response.send_message(
            "Rules acknowledged.",
            ephemeral=True
        )


class ProfileEditView(discord.ui.View):
    def __init__(
        self,
        bot,
        member,
        original_profile
    ):
        super().__init__(
            timeout=600
        )

        self.bot = bot
        self.member = member
        self.original_profile = original_profile

        self.birthday_month = original_profile["birthday_month"]
        self.birthday_day = original_profile["birthday_day"]
        self.birthday_year = original_profile["birthday_year"]

        self.pronouns = original_profile["pronouns"]
        self.pronoun_index = original_profile["pronoun_index"]

        self.nickname = original_profile["nickname"]
        self.timezone = original_profile["timezone"]

        self.rules_acknowledged = (
            original_profile["rules_acknowledged"]
        )

        self.add_item(
            PronounSelect(self)
        )

        self.add_item(
            TimezoneSelect(self)
        )

    def check_user(
        self,
        interaction: discord.Interaction
    ):
        return interaction.user.id == self.member.id

    @discord.ui.button(
        label="🎂 Birthday",
        style=discord.ButtonStyle.primary
    )
    async def birthday_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not self.check_user(interaction):
            await interaction.response.send_message(
                "This isn't your profile.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            BirthdayEditModal(self)
        )

    @discord.ui.button(
        label="🏷️ Nickname",
        style=discord.ButtonStyle.primary
    )
    async def nickname_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not self.check_user(interaction):
            await interaction.response.send_message(
                "This isn't your profile.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            NicknameEditModal(self)
        )

    @discord.ui.button(
        label="📜 Acknowledge Rules",
        style=discord.ButtonStyle.success
    )
    async def rules_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not self.check_user(interaction):
            await interaction.response.send_message(
                "This isn't your profile.",
                ephemeral=True
            )
            return

        self.rules_acknowledged = True

        await interaction.response.send_message(
            "Rules acknowledged.",
            ephemeral=True
        )

    @discord.ui.button(
        label="💾 Save",
        style=discord.ButtonStyle.success,
        row=4
    )
    async def save_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not self.check_user(interaction):
            await interaction.response.send_message(
                "This isn't your profile.",
                ephemeral=True
            )
            return

        if not self.rules_acknowledged:
            await interaction.response.send_message(
                "You must acknowledge the rules before saving.",
                ephemeral=True
            )
            return

        now = datetime.now(timezone.utc)

        original_values = (
            self.original_profile["birthday_month"],
            self.original_profile["birthday_day"],
            self.original_profile["birthday_year"],
            self.original_profile["pronouns"],
            self.original_profile["pronoun_index"],
            self.original_profile["nickname"],
            self.original_profile["timezone"],
        )

        new_values = (
            self.birthday_month,
            self.birthday_day,
            self.birthday_year,
            self.pronouns,
            self.pronoun_index,
            self.nickname,
            self.timezone,
        )

        changed = original_values != new_values

        last_edited = parse_timestamp(
            self.original_profile["profile_last_edited"]
        )

        if changed and last_edited is not None:
            cooldown = timedelta(days=7)

            if now - last_edited < cooldown:
                remaining = cooldown - (
                    now - last_edited
                )

                days = remaining.days
                hours = remaining.seconds // 3600

                await interaction.response.send_message(
                    f"You can edit your profile again in "
                    f"**{days} days and {hours} hours**.",
                    ephemeral=True
                )
                return

        self.bot.database.update_member_profile(
            interaction.guild.id,
            self.member.id,
            birthday_month=self.birthday_month,
            birthday_day=self.birthday_day,
            birthday_year=self.birthday_year,
            pronouns=self.pronouns,
            pronoun_index=self.pronoun_index,
            nickname=self.nickname,
            timezone=self.timezone,
            rules_acknowledged=True,
            profile_last_edited=(
                now.isoformat()
                if changed
                else self.original_profile["profile_last_edited"]
            )
        )

        try:
            await self.member.edit(
                nick=self.nickname,
                reason="Ratburn profile update"
            )
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        profile = self.bot.database.get_member_profile(
            interaction.guild.id,
            self.member.id
        )

        demerit_count = self.bot.database.get_demerit_count(
            interaction.guild.id,
            self.member.id
        )

        embed = build_profile_embed(
            self.member,
            profile,
            demerit_count
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

        self.stop()

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        row=4
    )
    async def cancel_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not self.check_user(interaction):
            await interaction.response.send_message(
                "This isn't your profile.",
                ephemeral=True
            )
            return

        profile = self.bot.database.get_member_profile(
            interaction.guild.id,
            self.member.id
        )

        demerit_count = self.bot.database.get_demerit_count(
            interaction.guild.id,
            self.member.id
        )

        embed = build_profile_embed(
            self.member,
            profile,
            demerit_count
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

        self.stop()


class ProfileView(discord.ui.View):
    def __init__(
        self,
        bot,
        member,
        profile
    ):
        super().__init__(
            timeout=600
        )

        self.bot = bot
        self.member = member
        self.profile = profile

    @discord.ui.button(
        label="✏️ Edit Profile",
        style=discord.ButtonStyle.primary
    )
    async def edit_profile(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "You can only edit your own profile.",
                ephemeral=True
            )
            return

        view = ProfileEditView(
            self.bot,
            self.member,
            self.profile
        )

        await interaction.response.edit_message(
            embed=build_profile_embed(
                self.member,
                self.profile,
                self.bot.database.get_demerit_count(
                    interaction.guild.id,
                    self.member.id
                )
            ),
            view=view
        )


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="profile",
        description="View your Ratburn profile."
    )
    async def profile(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return

        target = member or interaction.user

        profile = self.bot.database.get_member_profile(
            interaction.guild.id,
            target.id
        )

        demerit_count = self.bot.database.get_demerit_count(
            interaction.guild.id,
            target.id
        )

        own_profile = (
            target.id == interaction.user.id
        )

        embed = build_profile_embed(
            target,
            profile,
            demerit_count,
            own_profile=own_profile
        )

        view = None

        if own_profile:
            view = ProfileView(
                self.bot,
                target,
                profile
            )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Profile(bot))
