from math import floor
from discord import Embed
from discord.ext import tasks, commands

import utils


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.five_minute_loop.start()

    async def is_user_in_guild(self, guild, user_id):
        """Check if a user is in the guild."""
        try:
            await guild.fetch_member(user_id)
            return True
        except:
            return False

    async def update_leaderboard(self, channel_id, message_ids, sorted_ranks, embed_color, metric, label):
        """Helper function to update leaderboard for a given metric."""
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = self.bot.get_channel(channel_id)
        if not guild or not channel:
            return

        # Prepare the embed messages
        msg = await channel.fetch_message(message_ids[0])
        msg2 = await channel.fetch_message(message_ids[1])
        embed = Embed(color=embed_color)
        embed2 = Embed(color=embed_color)

        users = []
        for rank in sorted_ranks:
            user = self.bot.get_user(rank.user_id)
            if user and await self.is_user_in_guild(guild, user.id):
                if user.id == self.bot.user.id:
                    continue  # Skip bot's own ID
                users.append((user, rank))
            if len(users) == 10:  # Limit to top 10
                break

        text, text2 = [], []
        for index, (user, rank) in enumerate(users):
            line = f"#{index + 1} **{user.name}** ─── {metric(rank)}"
            if index < 5:
                text.append(line)
            else:
                text2.append(line)

        # Update embeds
        embed.description = '\n'.join(text)
        embed2.description = '\n'.join(text2)

        # Queue the first message edit
        await self.bot.message_edit_manager.queue_edit(
            message=msg,
            new_content=f"# {label} Leaderboard",
            new_embed=embed
        )

        # Queue the second message edit
        await self.bot.message_edit_manager.queue_edit(
            message=msg2,
            new_content=" ",  # Empty content
            new_embed=embed2
        )

    @tasks.loop(minutes=5)
    async def five_minute_loop(self):
        """Main loop to update all leaderboards every 5 minutes."""

        # Database check
        if not self.bot.connected:
            return

        #+ Level Leaderboard
        await self.update_leaderboard(
            channel_id=self.bot.config['channels']['leaderboard'],
            message_ids=[self.bot.config['leaderboard_messages']['1'], self.bot.config['leaderboard_messages']['2']],
            sorted_ranks=utils.Levels.sort_levels(),
            embed_color=0xFFBF00,
            metric=lambda rank: f"Lvl.{floor(rank.level):,}",
            label="Level"
        )

        #+ Coin Leaderboard
        await self.update_leaderboard(
            channel_id=self.bot.config['channels']['leaderboard'],
            message_ids=[self.bot.config['leaderboard_messages']['3'], self.bot.config['leaderboard_messages']['4']],
            sorted_ranks=utils.Currency.sort_coins(),
            embed_color=0x00FF00,
            metric=lambda rank: f"{self.bot.config['emojis']['coin']}{floor(rank.coins):,}x",
            label="Coin"
        )

        #+ Message Leaderboard
        await self.update_leaderboard(
            channel_id=self.bot.config['channels']['leaderboard'],
            message_ids=[self.bot.config['leaderboard_messages']['5'], self.bot.config['leaderboard_messages']['6']],
            sorted_ranks=utils.Tracking.sorted_messages(),
            embed_color=0xFF0000,
            metric=lambda rank: f"{rank.messages:,} msgs",
            label="Message"
        )

        #+ VC Hour Leaderboard
        await self.update_leaderboard(
            channel_id=self.bot.config['channels']['leaderboard'],
            message_ids=[self.bot.config['leaderboard_messages']['7'], self.bot.config['leaderboard_messages']['8']],
            sorted_ranks=utils.Tracking.sorted_vc_mins(),
            embed_color=0x0000FF,
            metric=lambda rank: f"{floor(rank.vc_mins / 60):,} hours",
            label="VC Hour"
        )

        #+ Daily Leaderboard
        await self.update_leaderboard(
            channel_id=self.bot.config['channels']['leaderboard'],
            message_ids=[self.bot.config['leaderboard_messages']['9'], self.bot.config['leaderboard_messages']['10']],
            sorted_ranks=utils.Daily.sorted_daily(),
            embed_color=0xFF00FF,
            metric=lambda rank: f"{rank.daily:,}th daily",
            label="Daily"
        )

    @five_minute_loop.before_loop
    async def before_five_minute_loop(self):
        """Wait until the bot is ready before running the loop."""
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Leaderboard(bot))
