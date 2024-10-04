from discord import Embed
from discord.ext import tasks
from discord.ext.commands import command, Cog, cooldown, BucketType, ApplicationCommandMeta
from random import choice, randint
from datetime import datetime as dt, timedelta
from calendar import day_name
from math import floor
import utils

class Seasonal(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.treats = ["🍬 Candy (Coins)", "🍫 Chocolate (Coins)", "🍭 Lollipop (Coins)", "🍪 Cookie (Coins)"]
        self.tricks = ["👻 Spooky Ghost (Lose Coins)", "🕷️ Spider (Lose Coins)", "💀 Skeleton (Lose Coins)", "🎃 Evil Pumpkin (Lose Coins)"]


    @cooldown(1, 7200, BucketType.user)  # 2-hour cooldown per user
    @command(application_command_meta=ApplicationCommandMeta())
    async def trick_or_treat(self, ctx):
        # Check if user is on cooldown
        if ctx.author in self.cooldowns and self.cooldowns[ctx.author] > dt.utcnow():
            remaining_time = self.cooldowns[ctx.author] - dt.utcnow()
            minutes = remaining_time.seconds // 60
            await ctx.send \
                (f"🎃 {ctx.author.mention}, you must wait {minutes} more minutes before trick-or-treating again!")
            return

        # Decide if user gets a treat or a trick
        outcome = choice(["treat", "trick"])

        if outcome == "treat":
            # User gets coins as a treat
            coins = randint(1000, 5000)  # Random amount of coins
            treat = choice(self.treats)
            await ctx.send \
                (f"🎉 {ctx.author.mention}, you went trick-or-treating and got a treat: {treat}! You earned {coins} coins!")
            await utils.CoinFunctions.earn(earner=ctx.author, amount=coins)

        else:
            # User loses coins as a trick
            coins = randint(2000, 5000)  # Random amount of coins lost
            trick = choice(self.tricks)
            await ctx.send \
                (f"😈 {ctx.author.mention}, you went trick-or-treating and got a trick: {trick}! You lost {coins} coins!")
            c = utils.Currency.get(ctx.author.id)
            c.coin -= coins
            async with self.bot.database() as db:
                await c.save(db)

        # Set the cooldown for the user
        self.cooldowns[ctx.author] = dt.utcnow() + timedelta(hours=2)


# The setup function to load the cog
def setup(bot):
    bot.add_cog(Seasonal(bot))
