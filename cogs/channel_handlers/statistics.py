from math import floor
from datetime import datetime as dt, timedelta
from discord import Embed
from discord.ext import tasks, commands

import utils

class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.five_minute_loop.start()

    @tasks.loop(minutes=5)
    async def five_minute_loop(self):
        """Main loop to update all statistics every 5 minutes."""
        guild = self.bot.get_guild(self.bot.config['guild_id'])

        # Get the stat channel and messages
        stat_channel = guild.get_channel(self.bot.config['channels']['statistics'])
        messages = [
            await stat_channel.fetch_message(self.bot.config['statistics_messages'][str(i)]) for i in range(1, 4)
        ]

        # Fix the economy if needed
        sc = utils.Currency.get(self.bot.user.id)
        total_coins = utils.Currency.get_total_coins()
        sc.coins += self.bot.config['total_coins'] - total_coins

        async with self.bot.database() as db:
            await sc.save(db)

        # Calculate statistics
        total_channels = len(guild.text_channels)
        total_roles = len(guild.roles)
        total_tix = utils.Currency.get_total_tickets()
        members = len(set(guild.members))

        # Role categories to evaluate
        supporter_roles = ['supporter', 'nitro', 'initiate', 'acolyte', 'ascended']
        roles_to_track = ['changelogs', 'scpsl', 'toxic', 'queer']

        role_stats = {role_name: len([m for m in guild.members if guild.get_role(self.bot.config['supporter_roles'][role_name]) in m.roles]) for role_name in supporter_roles}
        tracked_roles = {role_name: len([m for m in guild.members if guild.get_role(self.bot.config['ping_roles'].get(role_name, self.bot.config['access_roles'].get(role_name))) in m.roles]) for role_name in roles_to_track}

        # Economic calculations
        supporters_count = sum(role_stats.values())
        profit = role_stats['initiate'] * 9 + role_stats['acolyte'] * 18 + role_stats['ascended'] * 27

        inactive_count = len([m for m in guild.members if utils.Tracking.get(m.id).messages < 1])

        # Generate progress bars
        def generate_bar(percent):
            filled = round(percent / 10)
            return '▓' * filled + '▒' * (10 - filled)

        # Role statistics bars
        bars = {role_name: generate_bar((tracked_roles[role_name] / members) * 100) for role_name in tracked_roles}
        inactive_bar = generate_bar((inactive_count / members) * 100)

        # Generate cool embeds
        coin_emoji = self.bot.config['emojis']['coin']
        nitro_emoji = self.bot.config['emojis']['nitro']
        supporter_emojis = {role: self.bot.config['emojis'][role] for role in ['initiate', 'acolyte', 'ascended']}

        embed1 = Embed(
            title="**[- Supporter Statistics -]**",
            description=(
                f"💕 **Supporters**: {supporters_count-1:,}\n"
                f"{supporter_emojis['ascended']} **Ascended**: {role_stats['ascended']}\n"
                f"{supporter_emojis['acolyte']} **Acolyte**: {role_stats['acolyte']}\n"
                f"{supporter_emojis['initiate']} **Initiate**: {role_stats['initiate']}\n"
                f"{nitro_emoji} **Boosters**: {role_stats['nitro']}"
                f"Total Bills: **250$**\n"
                f"Donations: **{profit:,}$**\n"
                f"**Current Profit: {profit-250:,}$**"
            ),
            color=0xFF4500
        )

        embed2 = Embed(
            title="**[- Economy Statistics -]**",
            description=(
                f"{coin_emoji} **Total Coins**: {floor(total_coins):,}\n"
                f"🐍 **Serpent's Coins**: {floor(sc.coins):,}\n"
                f"🎟 **Current Tickets**: {floor(total_tix):,}"
            ),
            color=0x32CD32
        )

        embed3 = Embed(
            title="**[- Garden Statistics -]**",
            description=(
                f"👥 **Members**: {members:,}\n"
                f"📚 **Channels**: {total_channels:,}\n"
                f"🎭 **Roles**: {total_roles:,}\n\n"
                f"❌ **Inactive**: {inactive_count:,} ({round(inactive_count / members * 100)}%)\n{inactive_bar}\n"
                f"📝 **Changelog Subscribers**: {tracked_roles['changelogs']} ({round(tracked_roles['changelogs'] / members * 100)}%)\n{bars['changelogs']}\n"
                f"{self.bot.config['emojis']['scp']} **SCP:SL Players**: {tracked_roles['scpsl']} ({round(tracked_roles['scpsl'] / members * 100)}%)\n{bars['scpsl']}\n"
                f"🌺 **Degen Girls**: {tracked_roles['queer']} ({round(tracked_roles['queer'] / members * 100)}%)\n{bars['queer']}\n"
                f"🎮 **Toxic Gamers**: {tracked_roles['toxic']} ({round(tracked_roles['toxic'] / members * 100)}%)\n{bars['toxic']}\n"
            ),
            color=0x1E90FF
        )

        # List of messages and corresponding embeds
        messages_and_embeds = [
            (messages[0], embed1),
            (messages[1], embed2),
            (messages[2], embed3)
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


def setup(bot):
    bot.add_cog(Statistics(bot))
