from discord import Embed, RawReactionActionEvent
from discord.ext.commands import Cog
import utils


class RoleHandler(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def discord_log(self):
        """Server logs channel for logging events."""
        return self.bot.get_channel(self.bot.config['logs']['server'])

    async def fetch_roles_messages(self):
        """Fetch and update role messages in the roles channel."""
        ch = self.bot.get_channel(self.bot.config['channels']['roles'])
        role_messages = self.bot.config['roles_messages']

        embeds = [
            Embed(description=f"# Age\n```\nLying about your age will result in a ban!\n```\n"
                              f"> 🚬<@&{self.bot.config['age_roles']['adult']}>"
                              "`Doesn't give NSFW access, just says you're an adult!`\n"
                              f"> 🍼<@&{self.bot.config['age_roles']['underage']}>"
                              "`Given automatically if no age role selected.`\n"
                              f"> 🐾<@&{self.bot.config['access_roles']['nsfw']}>"
                              "`Access requires staff to give you this role after some kind of proof is provided.`", color=0x8f00f8),
            Embed(description=f"# Pings\n```\nGet notifications for things!\n```\n"
                              f"> 📔<@&{self.bot.config['ping_roles']['changelogs']}> `Recommended!`\n"
                              f"> ✅<@&{self.bot.config['ping_roles']['voters']}> `Get pinged for votes!`\n"
                              f"> 📆<@&{self.bot.config['ping_roles']['events']}> `Get pinged for events!`\n"
                              f"> 💀<@&{self.bot.config['ping_roles']['scp_ping']}> `Ping for SCP servers!`", color=0x8f00f8),
            Embed(description=f"# Identity\n```\nRoles that tell about you!\n```\n"
                              f"> 🎀<@&{self.bot.config['identity_roles']['trans']}>\n"
                              f"> 🪀<@&{self.bot.config['identity_roles']['non-binary']}>\n"
                              f"> 1️⃣<@&{self.bot.config['identity_roles']['monogamous']}>\n"
                              f"> 2️⃣<@&{self.bot.config['identity_roles']['polyamorous']}>\n"
                              f"> ♋<@&{self.bot.config['identity_roles']['autistic']}>\n", color=0x8f00f8),
            Embed(description=f"# Free Colors\n```\nThey are the worse colors though...\n```\n"
                              f"> 🧊<@&{self.bot.config['purchase_roles']['eww_blue']}>\n"
                              f"> 🍏<@&{self.bot.config['purchase_roles']['snot_green']}>\n"
                              f"> 🍌<@&{self.bot.config['purchase_roles']['yikes_yellow']}>", color=0x8f00f8)
        ]

        for i, embed in enumerate(embeds):
            msg = await ch.fetch_message(role_messages[str(i + 1)])
            await self.bot.message_edit_manager.queue_edit(
                message=msg,
                new_content=f" ",
                new_embed=embed
            )

        for msg_id in list(role_messages.values())[4:]:  # Fixed by converting to list
            msg = await ch.fetch_message(msg_id)
            await self.bot.message_edit_manager.queue_edit(
                message=msg,
                new_content=f"~",
            )

    @Cog.listener()
    async def on_ready(self):
        """Initial setup on bot ready event."""
        await self.fetch_roles_messages()

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        """Handle role addition when a reaction is added."""
        await self.handle_role_change(payload, add_role=True)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        """Handle role removal when a reaction is removed."""
        await self.handle_role_change(payload, add_role=False)

    async def handle_role_change(self, payload, add_role: bool):
        """Helper to handle adding/removing roles based on reactions."""
        if payload.channel_id != self.bot.config['channels']['roles']:
            return

        if self.bot.get_user(payload.user_id).bot:
            return

        emoji = payload.emoji.name if payload.emoji.is_unicode_emoji() else payload.emoji.id
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if not member:
            return

        role = await self.get_role(guild, emoji, member)
        if role:
            if add_role:
                await member.add_roles(role, reason="Reaction role added")
            else:
                await member.remove_roles(role, reason="Reaction role removed")

        # Manage reactions if needed
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if sum([i.count for i in message.reactions]) > 4000:
            await message.clear_reactions()
            for reaction in message.reactions:
                await message.add_reaction(reaction.emoji)

    async def get_role(self, guild, emoji, member):
        """Fetch the correct role based on the emoji reaction."""
        mod = utils.Moderation.get(member.id)
        roles = {
            "🚬": self.bot.config['age_roles']['adult'],
            "🍼": self.bot.config['age_roles']['underage'],
            "📔": self.bot.config['ping_roles']['changelogs'],
            "✅": self.bot.config['ping_roles']['voters'],
            "📆": self.bot.config['ping_roles']['events'],
            "💀": self.bot.config['ping_roles']['scp_ping'],
            "🎀": self.bot.config['identity_roles']['trans'],
            "🪀": self.bot.config['identity_roles']['non-binary'],
            "1️⃣": self.bot.config['identity_roles']['monogamous'],
            "2️⃣": self.bot.config['identity_roles']['polyamorous'],
            "♋": self.bot.config['identity_roles']['autistic'],
            #"🐾": self.bot.config['access_roles']['nsfw'] if not mod.child else None,
            "🧊": self.bot.config['purchase_roles']['eww_blue'],
            "🍏": self.bot.config['purchase_roles']['snot_green'],
            "🍌": self.bot.config['purchase_roles']['yikes_yellow']
        }

        role_id = roles.get(emoji)
        role = None
        if role_id:
            role = utils.DiscordGet(guild.roles, id=role_id)
            return role

        # Log if user fails to get role
        if not role:
            await member.send(f"Failed to get the role (probably due to age), please contact staff if this a mistake.")
            await self.discord_log.send(f"<@{member.id}> failed to get the role for emoji: {emoji}.")


def setup(bot):
    bot.add_cog(RoleHandler(bot))
