from discord.ext.commands import Cog
from discord import Embed, PartialEmoji, Message, RawReactionActionEvent
from datetime import datetime as dt
from asyncio import TimeoutError
import utils


class MailBox(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def archive_logs(self):
        """Retrieve the archive log channel."""
        return self.bot.get_channel(self.bot.config['logs']['archive'])

    @property
    def mailbox(self):
        """Retrieve the mailbox channel."""
        return self.bot.get_channel(self.bot.config['channels']['mailbox'])

    async def fetch_author(self, embed: Embed):
        """Fetch the author from the embed using their ID from the icon URL."""
        try:
            author_url = embed.author.icon_url
            author_id = int(author_url.split('/')[4])
            return self.bot.get_user(author_id)
        except (ValueError, IndexError) as e:
            print(f"Error fetching author from embed: {e}")
            return None

    async def send_to_author(self, author, content, embed=None):
        """Send a message to the author with optional embed content."""
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

        message = await self.mailbox.fetch_message(payload.message_id)
        if not message.embeds:
            return

        embed = message.embeds[0]
        if 'Verification' in embed.footer.text:
            await self.process_action('verification', message, payload.emoji, embed, payload)
        elif 'Artist' in embed.footer.text:
            await self.process_action('artist', message, payload.emoji, embed, payload)

    async def process_action(self, action_type: str, message: Message, emoji: PartialEmoji, embed: Embed, payload: RawReactionActionEvent):
        """Handles approval or denial actions based on emoji reaction for both artist and verification requests."""
        author = await self.fetch_author(embed)
        if not author:
            await message.delete()
            return

        if emoji.name == '✅':
            await self.handle_acceptance(action_type, author, message, embed, payload)
        elif emoji.name == '🔴':
            await self.handle_decline(action_type, author, message, embed, payload)

    async def handle_acceptance(self, action_type: str, author, message: Message, embed: Embed, payload: RawReactionActionEvent):
        """Processes approval actions for both artist and verification requests."""
        guild = message.guild
        embed.color = 0x008800  # Green color for acceptance
        embed.set_footer(text=f'{action_type.capitalize()} accepted on {dt.utcnow().strftime("%a %d %B %H:%M")}')

        # Archive the message in logs
        await self.archive_logs.send(f'Accepted by <@{payload.user_id}>.', embed=embed)

        # Notify the user
        if action_type == 'verification':
            await self.send_to_author(author, f"**You have been verified! Welcome to {guild.name}!**")
            await utils.UserFunctions.verify_user(user=author)
        elif action_type == 'artist':
            await self.send_to_author(author, f"**Your artist verification has been accepted!**\nPlease allow some time for your personal channel to be created.")

        await message.delete()

    async def handle_decline(self, action_type: str, author, message: Message, embed: Embed, payload: RawReactionActionEvent):
        """Processes denial actions for both artist and verification requests with optional reasoning."""
        channel = message.channel
        check = lambda m: m.channel == channel and m.author.id == payload.user_id
        reason_msg = await channel.send(f"Why are you declining this {action_type}?")

        try:
            reason_response = await self.bot.wait_for('message', check=check, timeout=60.0)
            reason = reason_response.content
            await reason_response.delete()
        except TimeoutError:
            reason = '<No reason given>'

        embed.color = 0x880000  # Red color for decline
        embed.set_footer(text=f'{action_type.capitalize()} declined on {dt.utcnow().strftime("%a %d %B %H:%M")}')

        # Archive the declined verification
        await self.archive_logs.send(f'Denied by <@{payload.user_id}> for reason: {reason}', embed=embed)

        # Notify the user
        await self.send_to_author(author, f"Your {action_type} request was declined for reason: `{reason}`.", embed=embed)

        await reason_msg.delete()
        await message.delete()


def setup(bot):
    bot.add_cog(MailBox(bot))
