import logging

import discord

logger = logging.getLogger("ratburn.reaction_roles.publishing")


async def publish_reaction_role_post(
    bot: discord.Client,
    guild: discord.Guild,
    post_id: int,
) -> tuple[bool, str]:

    database = bot.database
    post = database.get_reaction_role_post(post_id)

    if post is None or post["guild_id"] != guild.id:
        return False, "I couldn't find that reaction-role draft in this server."

    channel = guild.get_channel(post["channel_id"])

    if not isinstance(channel, discord.TextChannel):
        return False, "The destination channel is missing or unavailable."

    permissions = channel.permissions_for(guild.me)

    if not permissions.view_channel or not permissions.send_messages:
        return False, "I need permission to view the destination channel and send messages."

    if not permissions.embed_links or not permissions.add_reactions:
        return False, "I need **Embed Links** and **Add Reactions** permissions in the destination channel."

    entries = database.get_reaction_role_entries(post_id)

    if not entries:
        return False, "This draft has no role entries yet. Add at least one role first."

    embed = discord.Embed(
        title=post["title"],
        description=post["description"] or None,
        color=discord.Color.dark_teal(),
    )

    valid_entries = []

    for entry in entries:
        role = guild.get_role(entry["role_id"])

        if role is None or role.is_default() or role.managed:
            logger.warning(
                "Skipping unavailable reaction role %s in post %s.",
                entry["role_id"],
                post_id,
            )
            continue

        if role >= guild.me.top_role:
            logger.warning(
                "Skipping role %s because it is not below Ratburn's highest role.",
                role.id,
            )
            continue

        valid_entries.append(entry)

        if len(valid_entries) <= 25:
            embed.add_field(
                name=f"{entry['emoji']}  {role.name}",
                value=entry["description"] or "React below to receive this role.",
                inline=False,
            )

    if not valid_entries:
        return False, (
            "None of this draft's roles can currently be managed by Ratburn. "
            "Check that the roles exist and are below Ratburn's highest role."
        )

    if len(valid_entries) > 25:
        return False, (
            "Discord embeds support at most 25 fields. "
            "Please split this setup into multiple posts."
        )

    embed.set_footer(text="React to a role below to receive it. Remove your reaction to give it up.")

    message = None
    old_message_id = post["message_id"]

    if old_message_id:
        try:
            message = await channel.fetch_message(old_message_id)
        except discord.NotFound:
            message = None
        except discord.Forbidden:
            return False, "I can't access the existing post. Check my channel permissions."
        except discord.HTTPException:
            logger.exception("Couldn't fetch reaction-role message %s.", old_message_id)
            return False, "Discord couldn't retrieve the existing post."

    try:
        if message is None:
            message = await channel.send(embed=embed)
            database.update_reaction_role_post(
                post_id,
                "message_id",
                message.id,
            )
        else:
            await message.edit(embed=embed)

    except discord.Forbidden:
        return False, "Discord refused to publish the embed. Check my channel permissions."
    except discord.HTTPException:
        logger.exception("Couldn't publish reaction-role post %s.", post_id)
        return False, "Discord couldn't publish the post. Check Ratburn's logs."

    desired_emojis = [entry["emoji"] for entry in valid_entries]

    try:
        for emoji in desired_emojis:
            await message.add_reaction(emoji)

    except (discord.Forbidden, discord.HTTPException):
        logger.exception(
            "Post %s was published, but at least one reaction could not be added.",
            post_id,
        )
        return True, (
            f"Published the post in {channel.mention}, but Discord wouldn't let "
            "me add every reaction. Check Ratburn's **Add Reactions** permission "
            "and confirm the configured emojis are valid."
        )

    return True, f"Published the reaction-role menu in {channel.mention}!"
