import calendar
import json
from datetime import datetime, timezone

import discord
from discord.ext import commands

from cogs.profile.profile import build_profile_embed


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


async def return_to_profile(
    interaction: discord.Interaction,
    bot,
    member: discord.Member,
    profile_view
):
    profile = bot.database.get_member_profile(
        member.guild.id,
        member.id
    )

    demerit_count = bot.database.get_demerit_count(
        member.guild.id,
        member.id
    )

    embed = build_profile_embed(
        member,
        profile,
        demerit_count
    )

    await interaction.response.edit_message(
        content=None,
        embed=embed,
        view=profile_view
    )


class WelcomeView(discord.ui.View):
    def __init__(self, bot, member: discord.Member):
        super().__init__(timeout=None)

        self.bot = bot
        self.member = member

    @discord.ui.button(
        label="Get situated?",
        style=discord.ButtonStyle.primary
    )
    async def get_situated(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.defer()

        if interaction.user.id != self.member.id:
            await interaction.followup.send(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "onboarding_message_id",
            interaction.message.id
        )

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "onboarding_step",
            "birthday"
        )

        await interaction.edit_original_response(
            content=(
                "Excellent. Let's get a few things sorted out.\n\n"
                "First, when is your birthday?"
            ),
            view=BirthdayView(
                self.bot,
                self.member
            )
        )


class BirthdayView(discord.ui.View):
    def __init__(
        self,
        bot,
        member: discord.Member,
        profile_view=None
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.member = member
        self.profile_view = profile_view

        self.selected_month = None
        self.selected_day = None
        self.selected_year = None

        self.add_item(MonthSelect())

        self.day_button = DayButton()
        self.add_item(self.day_button)

        self.year_button = discord.ui.Button(
            label="Year (optional)",
            style=discord.ButtonStyle.secondary
        )
        self.year_button.callback = self.year_button_callback
        self.add_item(self.year_button)

        self.no_year_button = discord.ui.Button(
            label="No year",
            style=discord.ButtonStyle.secondary
        )
        self.no_year_button.callback = self.no_year_button_callback
        self.add_item(self.no_year_button)

        self.save_button = discord.ui.Button(
            label="Save Birthday",
            style=discord.ButtonStyle.success
        )
        self.save_button.callback = self.save_birthday
        self.add_item(self.save_button)

        if self.profile_view is not None:
            self.back_button = discord.ui.Button(
                label="Back to Profile",
                emoji="◀️",
                style=discord.ButtonStyle.secondary
            )
            self.back_button.callback = self.back_to_profile
            self.add_item(self.back_button)

    async def check_user(self, interaction: discord.Interaction):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return False

        return True

    async def back_to_profile(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await return_to_profile(
            interaction,
            self.bot,
            self.member,
            self.profile_view
        )

    async def year_button_callback(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await interaction.response.send_modal(
            YearModal(self)
        )

    async def no_year_button_callback(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        self.selected_year = None
        self.year_button.label = "Year (optional)"

        await interaction.response.edit_message(
            view=self
        )

    async def save_birthday(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        if self.selected_month is None:
            await interaction.response.send_message(
                "Please choose a month first.",
                ephemeral=True
            )
            return

        if self.selected_day is None:
            await interaction.response.send_message(
                "Please choose a day first.",
                ephemeral=True
            )
            return

        month = self.selected_month
        day = self.selected_day
        year = self.selected_year

        validation_year = year if year is not None else 2000
        max_day = calendar.monthrange(
            validation_year,
            month
        )[1]

        if day > max_day:
            await interaction.response.send_message(
                f"{calendar.month_name[month]} doesn't have "
                f"{day} days. Please choose another day.",
                ephemeral=True
            )
            return

        guild_id = self.member.guild.id
        user_id = self.member.id

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "birthday_month",
            month
        )

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "birthday_day",
            day
        )

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "birthday_year",
            year
        )

        if self.profile_view is not None:
            await return_to_profile(
                interaction,
                self.bot,
                self.member,
                self.profile_view
            )
            return

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "onboarding_step",
            "pronouns"
        )

        await interaction.response.edit_message(
            content=(
                "Birthday saved! 🎂\n\n"
                "Next question: what pronouns should I use for you?"
            ),
            view=PronounView(
                self.bot,
                self.member
            )
        )


class MonthSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=calendar.month_name[month],
                value=str(month)
            )
            for month in range(1, 13)
        ]

        super().__init__(
            placeholder="Choose your birth month...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        if interaction.user.id != view.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

        selected = self.values[0]
        view.selected_month = int(selected)

        for option in self.options:
            option.default = option.value == selected

        await interaction.response.edit_message(
            view=view
        )


class DayButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Choose Day",
            style=discord.ButtonStyle.secondary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        view = self.view

        if interaction.user.id != view.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            DayModal(view)
        )


class DayModal(
    discord.ui.Modal,
    title="Birthday Day"
):
    day = discord.ui.TextInput(
        label="Birth day",
        placeholder="Example: 15",
        min_length=1,
        max_length=2,
        required=True
    )

    def __init__(self, birthday_view):
        super().__init__()

        self.birthday_view = birthday_view

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != self.birthday_view.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

        try:
            day = int(self.day.value)
        except ValueError:
            await interaction.response.send_message(
                "Please enter a number from 1 to 31.",
                ephemeral=True
            )
            return

        if day < 1 or day > 31:
            await interaction.response.send_message(
                "Please enter a number from 1 to 31.",
                ephemeral=True
            )
            return

        self.birthday_view.selected_day = day
        self.birthday_view.day_button.label = f"Day: {day}"

        await interaction.response.edit_message(
            view=self.birthday_view
        )


class YearModal(discord.ui.Modal, title="Birthday Year"):
    year = discord.ui.TextInput(
        label="Birth year",
        placeholder="Example: 1994",
        min_length=4,
        max_length=4,
        required=True
    )

    def __init__(self, birthday_view: BirthdayView):
        super().__init__()

        self.birthday_view = birthday_view

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.birthday_view.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

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

        self.birthday_view.selected_year = year
        self.birthday_view.year_button.label = f"Year: {year}"

        await interaction.response.edit_message(
            view=self.birthday_view
        )


class PronounView(discord.ui.View):
    def __init__(
        self,
        bot,
        member: discord.Member,
        profile_view=None
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.member = member
        self.profile_view = profile_view
        self.selected_pronouns = None

        self.add_item(PronounSelect())

        self.custom_button = discord.ui.Button(
            label="Custom",
            style=discord.ButtonStyle.secondary
        )
        self.custom_button.callback = self.custom_pronoun_callback
        self.add_item(self.custom_button)

        self.save_button = discord.ui.Button(
            label="Save Pronouns",
            style=discord.ButtonStyle.success
        )
        self.save_button.callback = self.save_pronouns
        self.add_item(self.save_button)

        if self.profile_view is not None:
            self.back_button = discord.ui.Button(
                label="Back to Profile",
                emoji="◀️",
                style=discord.ButtonStyle.secondary
            )
            self.back_button.callback = self.back_to_profile
            self.add_item(self.back_button)

    async def check_user(self, interaction: discord.Interaction):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return False

        return True

    async def back_to_profile(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await return_to_profile(
            interaction,
            self.bot,
            self.member,
            self.profile_view
        )

    async def custom_pronoun_callback(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await interaction.response.send_modal(
            CustomPronounModal(self)
        )

    async def save_pronouns(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        if self.selected_pronouns is None:
            pronouns = PRONOUN_OPTIONS["they/them"]
        else:
            pronouns = self.selected_pronouns

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "pronouns",
            json.dumps(pronouns)
        )

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "pronoun_index",
            0
        )

        if self.profile_view is not None:
            await return_to_profile(
                interaction,
                self.bot,
                self.member,
                self.profile_view
            )
            return

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "onboarding_step",
            "nickname"
        )

        await interaction.response.edit_message(
            content=(
                "Pronouns saved!\n\n"
                "Now, what shall I call you?"
            ),
            view=NicknameView(
                self.bot,
                self.member
            )
        )


class PronounSelect(discord.ui.Select):
    def __init__(self):
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

        super().__init__(
            placeholder="Choose your pronouns...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        if interaction.user.id != view.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

        selected = self.values[0]

        for option in self.options:
            option.default = option.value == selected

        if selected == "ask me":
            view.selected_pronouns = PRONOUN_OPTIONS["they/them"]
        else:
            view.selected_pronouns = PRONOUN_OPTIONS[selected]

        await interaction.response.edit_message(
            view=view
        )


class CustomPronounModal(
    discord.ui.Modal,
    title="Custom Pronouns"
):
    pronouns = discord.ui.TextInput(
        label="Pronouns",
        placeholder="they/them or they",
        min_length=1,
        max_length=50,
        required=True
    )

    def __init__(self, pronoun_view: PronounView):
        super().__init__()

        self.pronoun_view = pronoun_view

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.pronoun_view.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

        value = self.pronouns.value.strip().lower()

        if "/" in value:
            parts = [
                part.strip()
                for part in value.split("/")
            ]

            if len(parts) != 2 or not all(parts):
                await interaction.response.send_message(
                    "Please enter pronouns in a format like "
                    "`she/her` or `they/them`.",
                    ephemeral=True
                )
                return

            subject, object_pronoun = parts
        else:
            subject = value
            object_pronoun = value

        self.pronoun_view.selected_pronouns = [
            {
                "subject": subject,
                "object": object_pronoun
            }
        ]

        await interaction.response.edit_message(
            view=self.pronoun_view
        )


class NicknameView(discord.ui.View):
    def __init__(
        self,
        bot,
        member: discord.Member,
        profile_view=None
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.member = member
        self.profile_view = profile_view

        self.nickname = None

        self.nickname_button = discord.ui.Button(
            label="Set Nickname",
            style=discord.ButtonStyle.secondary
        )
        self.nickname_button.callback = self.nickname_callback
        self.add_item(self.nickname_button)

        self.skip_button = discord.ui.Button(
            label="Keep Current Name",
            style=discord.ButtonStyle.secondary
        )
        self.skip_button.callback = self.skip_nickname
        self.add_item(self.skip_button)

        self.save_button = discord.ui.Button(
            label="Save Nickname",
            style=discord.ButtonStyle.success
        )
        self.save_button.callback = self.save_nickname
        self.add_item(self.save_button)

        if self.profile_view is not None:
            self.back_button = discord.ui.Button(
                label="Back to Profile",
                emoji="◀️",
                style=discord.ButtonStyle.secondary
            )
            self.back_button.callback = self.back_to_profile
            self.add_item(self.back_button)

    async def check_user(self, interaction: discord.Interaction):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return False

        return True

    async def back_to_profile(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await return_to_profile(
            interaction,
            self.bot,
            self.member,
            self.profile_view
        )

    async def nickname_callback(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await interaction.response.send_modal(
            NicknameModal(self)
        )

    async def skip_nickname(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        self.nickname = None
        self.nickname_button.label = "Set Nickname"

        await interaction.response.edit_message(
            view=self
        )

    async def save_nickname(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        guild_id = self.member.guild.id
        user_id = self.member.id

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "nickname",
            self.nickname
        )

        if self.nickname:
            try:
                await self.member.edit(
                    nick=self.nickname,
                    reason="Ratburn onboarding"
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I couldn't change your nickname. "
                    "Please check that Ratburn has permission to "
                    "manage your nickname.",
                    ephemeral=True
                )
                return
            except discord.HTTPException:
                await interaction.response.send_message(
                    "Something went wrong while changing your nickname. "
                    "Please try again.",
                    ephemeral=True
                )
                return

        if self.profile_view is not None:
            await return_to_profile(
                interaction,
                self.bot,
                self.member,
                self.profile_view
            )
            return

        self.bot.database.set_member_profile(
            guild_id,
            user_id,
            "onboarding_step",
            "timezone"
        )

        await interaction.response.edit_message(
            content=(
                "Nickname saved!\n\n"
                "Now, what timezone should I use for you?"
            ),
            view=TimezoneView(
                self.bot,
                self.member
            )
        )


class NicknameModal(
    discord.ui.Modal,
    title="Set Nickname"
):
    nickname = discord.ui.TextInput(
        label="Nickname",
        placeholder="What should Ratburn call you?",
        min_length=1,
        max_length=32,
        required=True
    )

    def __init__(self, nickname_view: NicknameView):
        super().__init__()

        self.nickname_view = nickname_view

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.nickname_view.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

        nickname = self.nickname.value.strip()

        if not nickname:
            await interaction.response.send_message(
                "Please enter a nickname.",
                ephemeral=True
            )
            return

        self.nickname_view.nickname = nickname
        self.nickname_view.nickname_button.label = nickname

        await interaction.response.edit_message(
            view=self.nickname_view
        )


class TimezoneView(discord.ui.View):
    def __init__(
        self,
        bot,
        member: discord.Member,
        profile_view=None
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.member = member
        self.profile_view = profile_view
        self.selected_timezone = None

        self.add_item(TimezoneSelect())

        self.save_button = discord.ui.Button(
            label="Save Timezone",
            style=discord.ButtonStyle.success
        )
        self.save_button.callback = self.save_timezone
        self.add_item(self.save_button)

        if self.profile_view is not None:
            self.back_button = discord.ui.Button(
                label="Back to Profile",
                emoji="◀️",
                style=discord.ButtonStyle.secondary
            )
            self.back_button.callback = self.back_to_profile
            self.add_item(self.back_button)

    async def check_user(self, interaction: discord.Interaction):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return False

        return True

    async def back_to_profile(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        await return_to_profile(
            interaction,
            self.bot,
            self.member,
            self.profile_view
        )

    async def save_timezone(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        if self.selected_timezone is None:
            await interaction.response.send_message(
                "Please choose a timezone first.",
                ephemeral=True
            )
            return

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "timezone",
            self.selected_timezone
        )

        if self.profile_view is not None:
            await return_to_profile(
                interaction,
                self.bot,
                self.member,
                self.profile_view
            )
            return

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "onboarding_step",
            "rules"
        )

        rules_view = RulesView(
            self.bot,
            self.member
        )

        await interaction.response.edit_message(
            content=(
                "Timezone saved!\n\n"
                "Nearly finished. Please read and acknowledge "
                "the server rules."
            ),
            view=rules_view
        )


class TimezoneSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=offset,
                description=name[:100],
                value=iana
            )
            for offset, name, iana in TIMEZONE_OPTIONS
        ]

        super().__init__(
            placeholder="Choose your timezone...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view

        if interaction.user.id != view.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return

        selected = self.values[0]
        view.selected_timezone = selected

        for option in self.options:
            option.default = option.value == selected

        await interaction.response.edit_message(
            view=view
        )


class RulesView(discord.ui.View):
    def __init__(
        self,
        bot,
        member: discord.Member
    ):
        super().__init__(timeout=None)

        self.bot = bot
        self.member = member

        config = self.bot.database.get_config(
            member.guild.id
        )

        rules_channel_id = config["rules_channel_id"]
        rules_message_id = config["rules_message_id"]

        if rules_channel_id and rules_message_id:
            rules_url = (
                f"https://discord.com/channels/"
                f"{member.guild.id}/"
                f"{rules_channel_id}/"
                f"{rules_message_id}"
            )

            self.add_item(
                discord.ui.Button(
                    label="Read the Rules",
                    emoji="📜",
                    style=discord.ButtonStyle.link,
                    url=rules_url
                )
            )

        self.acknowledge_button = discord.ui.Button(
            label="I Acknowledge the Rules",
            emoji="✅",
            style=discord.ButtonStyle.success
        )

        self.acknowledge_button.callback = (
            self.acknowledge_rules
        )

        self.add_item(self.acknowledge_button)

    async def check_user(
        self,
        interaction: discord.Interaction
    ):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This isn't your onboarding!",
                ephemeral=True
            )
            return False

        return True

    async def acknowledge_rules(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_user(interaction):
            return

        config = self.bot.database.get_config(
            self.member.guild.id
        )

        if not (
            config["rules_channel_id"]
            and config["rules_message_id"]
        ):
            await interaction.response.send_message(
                "The server rules haven't been configured yet. "
                "Please let a server administrator know.",
                ephemeral=True
            )
            return

        now = datetime.now(timezone.utc).isoformat()

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "rules_acknowledged",
            1
        )

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "rules_acknowledged_at",
            now
        )

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "onboarding_step",
            "completed"
        )

        self.bot.database.set_member_profile(
            self.member.guild.id,
            self.member.id,
            "onboarding_completed_at",
            now
        )

        new_member = self.bot.get_cog("NewMember")

        if new_member is not None:
            await new_member.remove_new_member_role(
                self.member
            )

        profile = self.bot.database.get_member_profile(
            self.member.guild.id,
            self.member.id
        )

        demerit_count = self.bot.database.get_demerit_count(
            self.member.guild.id,
            self.member.id
        )

        embed = build_profile_embed(
            self.member,
            profile,
            demerit_count
        )

        view = discord.ui.View(timeout=600)

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=view
        )


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = self.bot.database.get_config(member.guild.id)

        if not config["welcome_channel_id"]:
            return

        channel = member.guild.get_channel(
            config["welcome_channel_id"]
        )

        if channel is None:
            return

        message = await channel.send(
            content=(
                "Welcome! Just take a moment to get situated, "
                "if you please."
            ),
            view=WelcomeView(
                self.bot,
                member
            )
        )

        self.bot.database.set_member_profile(
            member.guild.id,
            member.id,
            "onboarding_message_id",
            message.id
        )

        self.bot.database.set_member_profile(
            member.guild.id,
            member.id,
            "onboarding_step",
            "welcome"
        )


async def setup(bot):
    await bot.add_cog(Welcome(bot))
