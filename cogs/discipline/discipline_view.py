import discord


class DisciplineRecordView(discord.ui.View):
    RECORDS_PER_PAGE = 3

    def __init__(
        self,
        owner_id: int,
        member: discord.Member,
        active_records,
        retired_records,
        active_demerits: int,
        lifetime_demerits: int,
        punishment_tier: str,
    ):
        super().__init__(timeout=300)

        self.owner_id = owner_id
        self.member = member
        self.active_records = list(active_records)
        self.retired_records = list(retired_records)
        self.active_demerits = active_demerits
        self.lifetime_demerits = lifetime_demerits
        self.punishment_tier = punishment_tier
        self.page = 0

        self.records = [
            (record, False)
            for record in self.active_records
        ] + [
            (record, True)
            for record in self.retired_records
        ]

        self.records.sort(
            key=lambda item: (
                item[0]["created_at"] or ""
            ),
            reverse=True
        )

        self.total_pages = max(
            1,
            (
                len(self.records) + self.RECORDS_PER_PAGE - 1
            ) // self.RECORDS_PER_PAGE
        )

        self.previous_button.disabled = True
        self.next_button.disabled = self.total_pages <= 1

    async def interaction_check(
        self,
        interaction: discord.Interaction
    ) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "These discipline records belong to another "
                "administrator's session.",
                ephemeral=True
            )
            return False

        return True

    def format_record(self, record) -> str:
        action = record["action"].replace("_", " ").title()
        reason = record["reason"] or "No reason provided."

        if len(reason) > 250:
            reason = reason[:247] + "..."

        lines = [
            f"**#{action}**",
            f"Reason: {reason}",
            f"Issued: {record['created_at']}",
        ]

        if record["expires_at"]:
            lines.append(f"Expires: {record['expires_at']}")

        status = record["status"]

        if status != "active":
            status = status.replace("_", " ").title()
            lines.append(f"Status: {status}")
        elif record["expires_at"]:
            lines.append("Status: Expired")

        return "\n".join(lines)

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"⚖️ Discipline Record: {self.member.display_name}",
            color=discord.Color.dark_gold()
        )

        embed.set_thumbnail(
            url=self.member.display_avatar.url
        )

        embed.add_field(
            name="Active Demerits",
            value=str(self.active_demerits),
            inline=True
        )

        embed.add_field(
            name="Lifetime Demerits",
            value=str(self.lifetime_demerits),
            inline=True
        )

        embed.add_field(
            name="Current Punishment Tier",
            value=self.punishment_tier,
            inline=True
        )

        start = self.page * self.RECORDS_PER_PAGE
        end = start + self.RECORDS_PER_PAGE
        page_records = self.records[start:end]

        active_entries = [
            self.format_record(record)
            for record, retired in page_records
            if not retired
        ]

        retired_entries = [
            self.format_record(record)
            for record, retired in page_records
            if retired
        ]

        embed.add_field(
            name="Active Records",
            value=(
                "\n\n".join(active_entries)
                if active_entries
                else "No active records on this page."
            ),
            inline=False
        )

        embed.add_field(
            name="Retired Records",
            value=(
                "\n\n".join(retired_entries)
                if retired_entries
                else "No retired records on this page."
            ),
            inline=False
        )

        embed.set_footer(
            text=(
                f"Page {self.page + 1} of {self.total_pages}"
                " • Records are sorted newest first"
            )
        )

        return embed

    async def update_page(
        self,
        interaction: discord.Interaction
    ):
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = (
            self.page >= self.total_pages - 1
        )

        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )

    @discord.ui.button(
        label="Previous",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.page > 0:
            self.page -= 1

        await self.update_page(interaction)

    @discord.ui.button(
        label="Next",
        emoji="▶️",
        style=discord.ButtonStyle.secondary
    )
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if self.page < self.total_pages - 1:
            self.page += 1

        await self.update_page(interaction)
