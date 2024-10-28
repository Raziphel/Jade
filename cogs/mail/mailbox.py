from discord.ext.commands import command, Cog
from discord import Embed, PartialEmoji, Message, RawReactionActionEvent, Guild
from datetime import datetime as dt
from asyncio import TimeoutError

import utils


class MailBox(Cog):

    def __init__(self, bot):
        self.bot = bot

    @property
    def archive_logs(self):
        """Retrieve archive log channel."""
        return self.bot.get_channel(self.bot.config['logs']['archive'])

    @property
    def mailbox(self):
        """Retrieve mailbox channel."""
        return self.bot.get_channel(self.bot.config['channels']['mailbox'])

    async def fetch_author(self, embed: Embed):
        """Fetches the author of the embed by extracting the user ID."""
        try:
            author_url = embed.author.icon_url
            author_id = int(author_url.split('/')[4])
            return self.bot.get_user(author_id)
        except (ValueError, IndexError) as e:
            print(f"Error fetching author from embed: {e}")
            return None

    async def send_to_author(self, author, content, embed=None):
        """Send a message to the author with optional embed."""
        try:
            if author:
                await author.send(content, embed=embed)
        except Exception as e:
            print(f"Failed to send message to user {author}: {e}")

    @Cog.listener('on_raw_reaction_add')
    async def mail_system(self, payload: RawReactionActionEvent):
        """Main handler for reaction events in the mailbox."""
        if payload.channel_id != self.mailbox.id:
            return

        user = self.bot.get_user(payload.user_id)
        if user is None or user.bot:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if not message.embeds:
            return

        embed = message.embeds[0]
        if 'Verification' in embed.footer.text:
            if payload.user_id in self.bot.helpers:
                await self.handle_verification(message, payload.emoji, embed, payload)

    async def handle_verification(self, message: Message, emoji: PartialEmoji, embed: Embed,
                                  payload: RawReactionActionEvent):
        """Handles the verification process based on the reaction emoji."""
        author = await self.fetch_author(embed)
        if not author:
            await message.delete()
            return

        if emoji.name == '✅':
            await self.accept_verification(author, message, embed, payload)
        elif emoji.name == '🔴':
            await self.decline_verification(author, message, embed, payload)

    async def accept_verification(self, author, message: Message, embed: Embed, payload: RawReactionActionEvent):
        """Process for accepting verification."""
        guild = message.guild
        embed.color = 0x008800  # Green color for accepted
        embed.set_footer(text=f'Verification archived on {dt.utcnow().strftime("%a %d %B %H:%M")}')

        # Archive the verification message
        await self.archive_logs.send(f'Archived by <@{payload.user_id}>.', embed=embed)

        # Notify the user
        await self.send_to_author(author, f"**You have been verified! Welcome to {guild.name}!**")

        # Verify the user
        await utils.UserFunction.verify_user(author)
        await message.delete()

    async def decline_verification(self, author, message: Message, embed: Embed, payload: RawReactionActionEvent):
        """Process for declining verification."""
        channel = message.channel
        check = lambda m: m.channel == channel and m.author.id == payload.user_id
        reason_msg = await channel.send("Why are you declining this verification?")

        try:
            reason_response = await self.bot.wait_for('message', check=check, timeout=60.0)
            reason = reason_response.content
            await reason_response.delete()
        except TimeoutError:
            reason = '<No reason given>'

        embed.color = 0x880000  # Red color for declined
        embed.set_footer(text=f'Verification declined on {dt.utcnow().strftime("%a %d %B %H:%M")}')

        # Archive the declined verification
        await self.archive_logs.send(f'Denied by <@{payload.user_id}> for reason: {reason}', embed=embed)

        # Notify the user
        await self.send_to_author(author, f"Your verification was declined for reason: `{reason}`.", embed=embed)

        await reason_msg.delete()
        await message.delete()


def setup(bot):
    bot.add_cog(MailBox(bot))
