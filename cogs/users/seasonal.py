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
        self.treats = ["🍬 Candy", "🍫 Chocolate", "🍭 Lollipop", "🍪 Cookie"]
        self.tricks = ["👻 Spooky Ghost", "🕷️ Spider", "💀 Skeleton", "🎃 Evil Pumpkin"]


    @cooldown(1, 7200, BucketType.user)  # 2-hour cooldown per user
    @command(application_command_meta=ApplicationCommandMeta())
    async def trick_or_treat(self, ctx):
        # Decide if user gets a treat or a trick
        outcome = choice(["treat", "trick"])

        if outcome == "treat":
            # User gets coins as a treat
            coins = randint(2000, 6000)  # Random amount of coins
            treat = choice(self.treats)
            await ctx.send \
                (f"**🎉 {ctx.author.mention}, you went trick-or-treating and got a treat: {treat}! You earned {coins} "
                 f"coins!**")
            await utils.CoinFunctions.earn(earner=ctx.author, amount=coins)

        else:
            # User loses coins as a trick
            coins = randint(1000, 4000)  # Random amount of coins lost
            trick = choice(self.tricks)
            await ctx.send \
                (f"**😈 {ctx.author.mention}, you went trick-or-treating and got a trick: {trick}! You lost {coins} "
                 f"coins!**")
            c = utils.Currency.get(ctx.author.id)
            c.coins -= coins
            async with self.bot.database() as db:
                await c.save(db)

        # Set the cooldown for the user
        self.cooldowns[ctx.author] = dt.utcnow() + timedelta(hours=2)


# The setup function to load the cog
def setup(bot):
    bot.add_cog(Seasonal(bot))
