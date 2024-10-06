from math import floor
from datetime import datetime as dt, timedelta
from discord import Embed
from discord.ext import tasks, commands
from collections import Counter

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

        # Active members in the last 7 days
        active_members_count = len([m for m in guild.members if (dt.utcnow() - m.joined_at).days <= 7])

        # Top 3 most active channels by message count
        channels_activity = Counter({ch.id: utils.Tracking.get_channel_message_count(ch.id) for ch in guild.text_channels})
        top_channels = channels_activity.most_common(3)
        top_channels_info = "\n".join([f"<#{ch_id}>: {msg_count:,} messages" for ch_id, msg_count in top_channels])

        # Total number of messages sent in the server
        total_message_count = sum(utils.Tracking.get_channel_message_count(ch.id) for ch in guild.text_channels)

        # Average user level
        total_levels = sum([utils.Levels.get(m.id).level for m in guild.members])
        average_level = round(total_levels / members, 2)

        # NEW: Top 3 roles with the most members
        role_member_counts = Counter({role.id: len(role.members) for role in guild.roles})
        top_roles = role_member_counts.most_common(3)
        top_roles_info = "\n".join([f"<@&{role_id}>: {count:,} members" for role_id, count in top_roles])

        # NEW: Join rates in the last 24 hours, 7 days, and 30 days
        join_24h = len([m for m in guild.members if (dt.utcnow() - m.joined_at) <= timedelta(hours=24)])
        join_7d = len([m for m in guild.members if (dt.utcnow() - m.joined_at) <= timedelta(days=7)])
        join_30d = len([m for m in guild.members if (dt.utcnow() - m.joined_at) <= timedelta(days=30)])

        # NEW: Command usage (track total commands and most-used commands)
        total_commands = utils.Tracking.get_total_commands()  # Hypothetical function to get the total commands used
        command_usage = utils.Tracking.get_most_used_commands(last_hours=24)  # Hypothetical function for command usage
        top_commands_info = "\n".join([f"{cmd}: {count} uses" for cmd, count in command_usage])

        # Generate progress bars
        def generate_bar(percent):
            filled = round(percent / 10)
            return '▓' * filled + '▒' * (10 - filled)

        # Role statistics bars
        bars = {role_name: generate_bar((tracked_roles[role_name] / members) * 100) for role_name in roles_to_track}
        inactive_bar = generate_bar((inactive_count / members) * 100)

        # Generate cool embeds
        coin_emoji = self.bot.config['emojis']['coin']
        nitro_emoji = self.bot.config['emojis']['nitro']
        supporter_emojis = {role: self.bot.config['emojis'][role] for role in ['initiate', 'acolyte', 'ascended']}

        embed1 = Embed(
            title="**[- Supporter Statistics -]**",
            description=(
                f"💕 **Supporters**: {supporters_count:,}\n"
                f"{supporter_emojis['ascended']} **Ascended**: {role_stats['ascended']}\n"
                f"{supporter_emojis['acolyte']} **Acolyte**: {role_stats['acolyte']}\n"
                f"{supporter_emojis['initiate']} **Initiate**: {role_stats['initiate']}\n"
                f"{nitro_emoji} **Boosters**: {role_stats['nitro']}"
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
                f"🌺 **Queer/Toxic Players**: {tracked_roles['queer']} ({round(tracked_roles['queer'] / members * 100)}%)\n{bars['queer']}\n\n"
                f"📝 **Top Channels**:\n{top_channels_info}\n"
                f"📊 **Total Messages**: {total_message_count:,}\n"
                f"⚖️ **Average User Level**: {average_level}\n"
                f"🔥 **Active Members (last 7 days)**: {active_members_count:,}\n\n"
                f"👑 **Top Roles**:\n{top_roles_info}\n\n"
                f"📈 **Join Rates**:\n"
                f"⏱️ Last 24h: {join_24h:,}\n"
                f"⏳ Last 7 days: {join_7d:,}\n"
                f"📅 Last 30 days: {join_30d:,}\n\n"
                f"⚔️ **Total Commands Used**: {total_commands:,}\n"
                f"🛠️ **Top Commands (Last 24h)**:\n{top_commands_info}"
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
