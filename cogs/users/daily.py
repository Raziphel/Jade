from discord import Embed
from discord.ext import tasks
from discord.ext.commands import command, Cog, cooldown, BucketType, ApplicationCommandMeta
from random import choice
from datetime import datetime as dt, timedelta
from calendar import day_name
from math import floor
from random import randint
import utils


class Daily(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_reset_checker.start()  # Start the task when the cog is loaded

    def cog_unload(self):
        self.daily_reset_checker.cancel()  # Stop the task when the cog is unloaded

    @tasks.loop(hours=8)
    async def daily_reset_checker(self):
        """Checks for users who have missed their daily reward and resets their daily streak."""
        await self.bot.wait_until_ready()

        guild = self.bot.get_guild(self.bot.config['guild_id'])
        now = dt.utcnow()

        for user in guild.members:
            day = utils.Daily.get(user.id)
            item = utils.Items.get(user.id)

            # Check if the user has missed their daily
            if (day.last_daily + timedelta(hours=48)) <= now:
                if item.daily_saver > 0:
                    item.daily_saver -= 1
                    await user.send(embed=utils.Embed(title="You have lost a daily saver for missing your daily!",
                                                      desc="Be sure to go claim it now!  As you only have 24 hours."))
                    day.last_daily = dt.utcnow() - timedelta(hours=22)
                else:
                    day.daily = 0  # Reset streak
                async with self.bot.database() as db:
                    await day.save(db)
                    await item.save(db)

    @daily_reset_checker.before_loop
    async def before_reset_checker(self):
        """Ensure the bot is ready before running the task."""
        await self.bot.wait_until_ready()

    @property
    def coin_logs(self):
        """Logs for coin transactions."""
        return self.bot.get_channel(self.bot.config['logs']['coins'])

    @cooldown(1, 30, BucketType.user)
    @command(application_command_meta=ApplicationCommandMeta())
    async def daily(self, ctx):
        """Claim your daily rewards!"""
        # Load user data
        day = utils.Daily.get(ctx.author.id)
        lvl = utils.Levels.get(ctx.author.id)
        currency = utils.Currency.get(ctx.author.id)
        item = utils.Items.get(ctx.author.id)
        track = utils.Tracking.get(ctx.author.id)

        # Initialize daily data if first time
        if not day.daily:
            day.daily = 1
            day.last_daily = dt.utcnow() - timedelta(hours=48)

        # Check if the daily reward was already claimed
        if (day.last_daily + timedelta(hours=23)) > dt.utcnow():
            remaining_time = day.last_daily + timedelta(hours=23) - dt.utcnow()
            hours, minutes = divmod(remaining_time.seconds, 3600)
            minutes //= 60
            return await ctx.send(embed=utils.Embed(
                desc=f"⏰ You've already claimed your daily rewards!\n"
                     f"**You can claim again in {hours} hours and {minutes} minutes.**",
                user=ctx.author))

        # Handle missed dailies or resetting the streak
        if (day.last_daily + timedelta(hours=48)) <= dt.utcnow():
            if item.daily_saver > 0:
                item.daily_saver -= 1
                await ctx.send(embed=utils.Embed(title="You have lost a daily saver for missing your daily!"))
                day.last_daily = dt.utcnow()  # Update last claim to now, without adjusting 22 hours
            else:
                day.daily = 1  # Reset streak
        else:
            day.daily += 1
        day.last_daily = dt.utcnow()

        # Calculate base reward
        base_reward = 25 + ((day.daily-1) * 2.15)
        if base_reward > 2500:
            base_reward = randint(2500, 3000)
        total_reward = base_reward  # Initial reward

        # Automatic milestone detection
        milestone_bonus = self.check_milestone(day.daily)
        total_reward += milestone_bonus

        # Random chance to get a bonus item (10% chance)
        if randint(1, 10) == 1:
            bonus_coins = 2000
            total_reward += bonus_coins
            await ctx.send(f"🎉 **Lucky!** You got an extra **{bonus_coins} coins** as a bonus today!")

        # Reward the user
        await utils.CoinFunctions.earn(earner=ctx.author, amount=total_reward)

        # Get ordinal suffix (st, nd, rd, th)
        def ordinal_suffix(n):
            if 10 <= n % 100 <= 20:
                return "th"
            else:
                return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

        ordinal = ordinal_suffix(day.daily)

        # Build the embed message
        embed = Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"# **This is your {day.daily}{ordinal} daily in a row!**",
            color=track.color  # Pretty color!
        )
        embed.add_field(
            name="💰 Coins Earned",
            value=f"**{self.bot.config['emojis']['coin']}{floor(total_reward):,} coins**",
            inline=False
        )

        # If the user hit a milestone, show it in the embed
        if milestone_bonus:
            embed.add_field(
                name="🌟 Milestone Reached!",
                value=f"**Congrats!** You've earned an extra **{milestone_bonus} coins** for hitting a milestone!",
                inline=False
            )

        embed.set_footer(text=f"Claimed by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        # Send the embed message
        await ctx.send(embed=embed)

        # Log the transaction
        await self.coin_logs.send(
            f"**{ctx.author.name} claimed their {day.daily}{ordinal} daily reward!**\n"
            f"Reward: {self.bot.config['emojis']['coin']}{floor(total_reward):,} coins"
        )

        # Save the data
        async with self.bot.database() as db:
            await day.save(db)
            await lvl.save(db)
            await currency.save(db)

    # Milestone check function (automated for intervals)
    def check_milestone(self, streak):
        """Automatically calculates milestone rewards based on streak length."""
        milestone_bonus = 0

        # Predefined major milestones
        if streak == 30:
            milestone_bonus = 1000  # 1 month milestone
        elif streak == 90:
            milestone_bonus = 3000  # 3 month milestone
        elif streak == 180:
            milestone_bonus = 5000  # 6 month milestone
        elif streak == 365:
            milestone_bonus = 10000  # 1 year milestone
        else:
            # For every additional 365 days, increase reward by 10,000
            if streak > 365 and (streak % 365 == 0):
                years_passed = streak // 365
                milestone_bonus = 10000 + (10000 * (years_passed - 1))  # +10,000 for every extra year after the first

        return milestone_bonus

# Register the cog
def setup(bot):
    bot.add_cog(Daily(bot))