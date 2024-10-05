# Discord
from discord.ext.commands import Cog
from discord import Embed
from discord.utils import get
import utils

# Additions
from re import search
from asyncio import sleep


class MusicRepostHandler(Cog):
    SPOTIFY_REGEX = r"^https:\/\/open\.spotify\.com.*"  # Spotify URL regex pattern

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message):
        """Detects Spotify music links and reposts them to a specific music channel."""

        guild = self.bot.get_guild(self.bot.config['guild_id'])  # Fetch the guild once
        music_channel = self.bot.get_channel(self.bot.config['channels']['music'])

        # Ignore DMs and bot messages
        if message.guild is None or message.author.bot:
            return

        # Only repost Spotify links
        if search(self.SPOTIFY_REGEX, message.content):

            # If the message is already in the music channel, ignore it
            if message.channel.id == music_channel.id:
                return

            # Create an embed to repost the message more cleanly
            embed = Embed(
                title="🎶 Music Repost",
                description=f"**{message.author.name}** shared a song in <#{message.channel.id}>!",
                color=0x1DB954,  # Spotify green color
                timestamp=message.created_at
            )
            embed.add_field(name="Link", value=message.content, inline=False)
            embed.set_footer(text="Posted via music repost bot")
            embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)

            try:
                await music_channel.send(embed=embed)
            except Exception as e:
                # Log any errors in the reposting process
                await self.bot.get_channel(self.bot.config['channels']['bot_log']).send(
                    f"Failed to repost music link: {str(e)}"
                )


def setup(bot):
    bot.add_cog(MusicRepostHandler(bot))
