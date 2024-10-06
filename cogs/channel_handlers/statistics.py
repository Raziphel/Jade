from math import floor
from asyncio import sleep
from datetime import datetime as dt, timedelta
from random import randint, choice

from discord import Game, Embed
from discord.ext import tasks
from discord.ext.commands import Cog

import utils

class Statistics(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.five_minute_loop.start()


    @tasks.loop(minutes=5)
    async def five_minute_loop(self):
        """Main loop to update all statistics every 5 minutes."""

        guild = self.bot.get_guild(self.bot.config['guild_id']) #? Guild

        # + This is the Statistics Channels
        ch = guild.get_channel(self.bot.config['channels']['statistics'])  # ? Stat Channel

        msg1 = await ch.fetch_message(self.bot.config['statistics_messages']['1'])
        msg2 = await ch.fetch_message(self.bot.config['statistics_messages']['2'])
        msg3 = await ch.fetch_message(self.bot.config['statistics_messages']['3'])

        # + Fix the economy!
        sc = utils.Currency.get(self.bot.user.id)
        total_coins = utils.Currency.get_total_coins()
        difference = self.bot.config['total_coins'] - total_coins

        sc.coins += difference
        async with self.bot.database() as db:
            await sc.save(db)

        total_channels = 0
        for channel in guild.text_channels:
            total_channels += 1

        total_roles = 0
        for role in guild.roles:
            total_roles += 1

        total_tix = utils.Currency.get_total_tickets()
        members = len(set(self.bot.get_all_members()))

        # ! THE FOR USER LOOP
        supporters = utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['supporter'])
        nitro = utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['nitro'])
        t1 = utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['initiate'])
        t2 = utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['acolyte'])
        t3 = utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['ascended'])
        # ? Statistical
        changelog = utils.DiscordGet(guild.roles, id=self.bot.config['ping_roles']['changelogs'])
        scpsl = utils.DiscordGet(guild.roles, id=self.bot.config['access_roles']['scpsl'])
        #minecraft = utils.DiscordGet(guild.roles, id=self.bot.config['access_roles']['supporters'])
        toxic = utils.DiscordGet(guild.roles, id=self.bot.config['access_roles']['toxic'])
        queer = utils.DiscordGet(guild.roles, id=self.bot.config['access_roles']['queer'])

        supps = 0
        profit = 0
        nitros = 0
        t1s = 0
        t2s = 0
        t3s = 0
        hims = 0
        hers = 0
        thems = 0
        changes = 0
        scpsl_ers = 0
        mc_ers = 0
        closed_garden_ers = 0
        inactive = 0

        for user in guild.members:
            # ? Generate Donator Stats
            if nitro in user.roles:
                nitros += 1
                supps += 1
            if t1 in user.roles:
                profit += 9
                t1s += 1
                supps += 1
            if t2 in user.roles:
                profit += 18
                t2s += 1
                supps += 1
            if t3 in user.roles:
                profit += 27
                t3s += 1
                supps += 1


            # ? Generate Role Stats
            if changelog in user.roles:
                changes += 1
            if scpsl in user.roles:
                scpsl_ers += 1
            #if minecraft in user.roles:
            #    mc_ers += 1
            if toxic in user.roles:
                closed_garden_ers += 1
            if queer in user.roles:
                closed_garden_ers += 1

            tr = utils.Tracking.get(user.id)
            if tr.messages < 1:
                inactive += 1

        # ? Generate the bars
        # ? Role Stats Bar
        changelog_bar = await self.generate_bar(percent=changes / members * 100)
        scpsl_bar = await self.generate_bar(percent=scpsl_ers / members * 100)
        mc_bar = await self.generate_bar(percent=mc_ers / members * 100)
        queer_bar = await self.generate_bar(percent=closed_garden_ers / members * 100)

        inactive_bar = await self.generate_bar(percent=inactive / members * 100)

        # ? Emojis
        coin_e = self.bot.config['emojis']['coin']
        scp_e = self.bot.config['emojis']['scp']
        initiate_e = self.bot.config['emojis']['initiate']
        acolyte_e = self.bot.config['emojis']['acolyte']
        ascended_e = self.bot.config['emojis']['ascended']
        nitro_e = self.bot.config['emojis']['nitro']
        #mc_e = "<:minecraft:1095414533041946724>"

        embed1 = Embed(title=f"**[- Supporter Statistics! -]**",
                       description=f"**This show's stats about server support!**\n\n"
                                   f"💕 Supporters: **{supps:,}**\n"
                                   f"{ascended_e} Ascended: **{t3s}**\n"
                                   f"{acolyte_e} Acolyte: **{t2s}**\n"
                                   f"{initiate_e} Initiate: **{t1s}**\n"
                                   f"{nitro_e} Boosters: **{nitros}**",
                       color=0xFF0000)

        embed2 = Embed(title=f"**[- Economy Statistics! -]**",
                       description=f"**This show's all the aspects of the Serpent's Economy!**\n\n{coin_e} Total: **{floor(total_coins):,}** Coins\n🐍 Serpent's: **{floor(sc.coins):,}** Coins\n🎟 Current Tickets: **{floor(total_tix):,}**",
                       color=0x00FF00)

        embed3 = Embed(title=f"**[- Garden Statistics! -]**",
                       description=f"**This show's stats about the Discord Server!**\n\n👥 Members: **"
                                   f"{members:,}**\n📚 Channels: **{total_channels:,}**\n 🎭 Roles: **"
                                   f"{total_roles:,}**\n\n❌ % Inactive: **{round(inactive / members * 100)}%**\n**"
                                   f"{inactive_bar}**\n📝 % Gets Changelogs: **{round(changes / members * 100)}%**\n**{changelog_bar}**\n{scp_e} % SCP:SL: **{round(scpsl_ers / members * 100)}%**\n**{scpsl_bar}**\n🌺 % Degen Girls: **{round(closed_garden_ers / members * 100)}%**\n**{queer_bar}**",
                       color=0x0000FF)

        # List of messages and corresponding embeds
        messages_and_embeds = [
            (msg1, embed1),
            (msg2, embed2),
            (msg3, embed3)
        ]

        # Loop through the messages and queue edits
        for message, embed in messages_and_embeds:
            await self.bot.message_edit_manager.queue_edit(
                message=message,
                new_content=" ",
                new_embed=embed
            )

    @five_minute_loop.before_loop
    async def before_five_minute_loop(self):
        """Wait until the bot is ready before running the loop."""
        await self.bot.wait_until_ready()



    async def generate_bar(self, percent):
        if percent < 5:
            return "▒▒▒▒▒▒▒▒▒▒"
        elif percent < 10:
            return "▓▒▒▒▒▒▒▒▒▒"
        elif percent < 20:
            return "▓▓▒▒▒▒▒▒▒▒"
        elif percent < 30:
            return "▓▓▓▒▒▒▒▒▒▒"
        elif percent < 40:
            return "▓▓▓▓▒▒▒▒▒▒"
        elif percent < 50:
            return "▓▓▓▓▓▒▒▒▒▒"
        elif percent < 60:
            return "▓▓▓▓▓▓▒▒▒▒"
        elif percent < 70:
            return "▓▓▓▓▓▓▓▒▒▒"
        elif percent < 80:
            return "▓▓▓▓▓▓▓▓▒▒"
        elif percent < 90:
            return "▓▓▓▓▓▓▓▓▓▒"
        elif percent > 95:
            return "▓▓▓▓▓▓▓▓▓▓"





def setup(bot):
    x = Statistics(bot)
    bot.add_cog(x)