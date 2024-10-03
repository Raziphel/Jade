from discord import Embed
from discord.ext import tasks
from discord.ext.commands import command, Cog, cooldown, BucketType, ApplicationCommandMeta
from random import choice
from datetime import datetime as dt, timedelta
from calendar import day_name
from math import floor
import utils


class Daily(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_reset_checker.start()  # Start the task when the cog is loaded

    def cog_unload(self):
        self.daily_reset_checker.cancel()  # Stop the task when the cog is unloaded

    @tasks.loop(hours=24)  # Check once a day
    async def daily_reset_checker(self):
        """Checks for users who have missed their daily reward and resets their daily streak."""
        await self.bot.wait_until_ready()

        # Get the current time
        now = dt.utcnow()

        guild = self.bot.get_guild(self.bot.config['guild_id'])

        # Loop through each user and check their last daily claim
        for user in guild.members:
            day = utils.Daily.get(user.id)

            # Check if the user has missed their daily
            if (day.last_daily + timedelta(days=3)) <= dt.utcnow():
                # Reset their daily streak/counter
                user.daily = 0

                # Save the update to the database
                async with self.bot.database() as db:
                    await user.save(db)

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
        """Claim your daily rewards."""
        # Load user data
        day = utils.Daily.get(ctx.author.id)
        lvl = utils.Levels.get(ctx.author.id)
        currency = utils.Currency.get(ctx.author.id)

        # Initialize daily data if first time
        if not day.daily:
            day.daily = 1
            day.last_daily = dt.utcnow() - timedelta(days=3)

        # Check if the daily reward was already claimed
        if (day.last_daily + timedelta(hours=22)) > dt.utcnow():
            remaining_time = day.last_daily + timedelta(hours=22) - dt.utcnow()
            hours, minutes = divmod(remaining_time.seconds, 3600)
            minutes //= 60
            return await ctx.send(embed=utils.Embed(
                desc=f"⏰ You've already claimed your daily rewards!\n"
                     f"**You can claim them again in {hours} hours and {minutes} minutes.**",
                user=ctx.author))

        # Handle missed dailies or resetting the streak
        if (day.last_daily + timedelta(days=3)) <= dt.utcnow():
            day.daily = 1
        else:
            day.daily += 1
        day.last_daily = dt.utcnow()

        # Cap daily rewards at 350 days
        streak = min(day.daily, 350)
        coins = 2.5 * ((10 + streak) * dt.utcnow().isoweekday())

        # Reward the user
        await utils.CoinFunctions.earn(earner=ctx.author, amount=coins)

        # Get the ordinal suffix (st, nd, rd, th)
        def ordinal_suffix(n):
            if 10 <= n % 100 <= 20:
                return "th"
            else:
                return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

        ordinal = ordinal_suffix(day.daily)
        weekday = day_name[dt.today().weekday()]

        # Send success message to the user
        await ctx.send(embed=utils.Embed(
            desc=f"# **This is your {day.daily}{ordinal} daily claimed in a row!**\n"
                 f"```\nYou have been rewarded:\n```"
                 f"***{self.bot.config['emojis']['coin']}{floor(coins):,} coins***",
            user=ctx.author))

        # Log the transaction
        await self.coin_logs.send(
            f"**{ctx.author.name} claimed their {day.daily}{ordinal} daily reward!**\n"
            f"Reward: {self.bot.config['emojis']['coin']}{floor(coins):,} coins")

        # Save the data changes
        async with self.bot.database() as db:
            await day.save(db)
            await lvl.save(db)
            await currency.save(db)

# Register the cog
def setup(bot):
    bot.add_cog(Daily(bot))
