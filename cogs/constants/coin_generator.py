from discord import Message
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from more_itertools import unique_everseen

from random import choice
from datetime import datetime as dt, timedelta
from re import compile

import utils

class Coin_Generator(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_gen_loop.start()
        self.valid_uri = compile(r"(\b(https?|ftp|file)://)?[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]")

    @Cog.listener('on_message')
    async def coin_generator(self, message: Message):
        """Determine Level progression settings based on messages."""

        # Ignore DMs, bot messages, and check if DB is connected
        if message.guild is None or message.author.bot or not self.bot.connected:
            return

        # Load user data
        lvl = utils.Levels.get(message.author.id)
        currency = utils.Currency.get(message.author.id)
        tracking = utils.Tracking.get(message.author.id)

        if lvl.last_xp is None:
            lvl.last_xp = dt.utcnow()

        # Ensure message isn't spammed within 10 seconds
        if (lvl.last_xp + timedelta(seconds=10)) <= dt.utcnow():
            # Calculate experience and unique words
            exp = 1
            unique_words = len(list(unique_everseen(message.content.split(), str.lower)))
            if message.attachments:
                unique_words += 10

            # Cap unique words to prevent excessive rewards
            unique_words = min(unique_words, 15)

            # Earn coins and experience points
            await utils.CoinFunctions.earn(earner=message.author, amount=unique_words)
            exp += 5 + unique_words

            # Level up user
            await utils.UserFunctions.level_up(user=message.author, channel=message.channel)

            # Update user data
            lvl.exp += exp + 5
            lvl.last_xp = dt.utcnow()
        tracking.messages += 1

        # Save user data in a single database transaction
        async with self.bot.database() as db:
            await lvl.save(db)
            await currency.save(db)
            await tracking.save(db)

    def cog_unload(self):
        """Cancel the voice generation loop when the cog is unloaded."""
        self.voice_gen_loop.cancel()

    @loop(minutes=10)
    async def voice_gen_loop(self):
        """Distribute coins and experience points to users in voice channels."""
        if not self.bot.connected:
            return

        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                for member in vc.members:
                    tracking = utils.Tracking.get(member.id)
                    tracking.vc_mins += 10

                    # Skip certain conditions like deafened or bots
                    if any([member.voice.deaf, member.voice.mute, member.voice.self_deaf, member.voice.afk, member.bot]):
                        continue
                    if len(vc.members) < 2:
                        continue

                    # Update coins and experience based on voice activity
                    currency = utils.Currency.get(member.id)
                    lvl = utils.Levels.get(member.id)
                    lvl.exp += (10 + len(vc.members))
                    await utils.CoinFunctions.earn(earner=member, amount=10 + (len(vc.members)*3))

                    await utils.UserFunctions.level_up(user=member, channel=None)

                    # Save updated data
                    async with self.bot.database() as db:
                        await currency.save(db)
                        await lvl.save(db)
                        await tracking.save(db)


    @voice_gen_loop.before_loop
    async def before_voice_gen_loop(self):
        """Ensure the bot is ready before starting the voice generation loop."""
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Coin_Generator(bot))
