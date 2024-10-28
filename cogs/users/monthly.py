
# Additions
from datetime import datetime as dt, timedelta

# Discord
from discord import Embed
from discord.ext.commands import command, Cog, ApplicationCommandMeta

import utils


class Monthly(Cog):

    def __init__(self, bot):
        self.bot = bot

    @property
    def coin_logs(self):
        """Logs for coin transactions."""
        return self.bot.get_channel(self.bot.config['logs']['coins'])


    @command(application_command_meta=ApplicationCommandMeta())
    async def monthly(self, ctx):
        """Supporters monthly claim of rewards!"""

        guild = self.bot.get_guild(self.bot.config['guild_id'])
        day = utils.Daily.get(ctx.author.id)
        c = utils.Currency.get(ctx.author.id)

        # Retrieve supporter roles
        supporter_roles = {
            "Nitro": utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['nitro']),
            "Initiate": utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['initiate']),
            "Acolyte": utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['acolyte']),
            "Ascended": utils.DiscordGet(guild.roles, id=self.bot.config['supporter_roles']['ascended'])
        }
        # Check if user has a supporter role
        supporter = any(role in ctx.author.roles for role in supporter_roles.values())

        if not supporter:
            await ctx.interaction.response.send_message("🚫 **Only supporters can claim a monthly reward!**")
            return

        # Initialize monthly claim date if not set
        if day.monthly is None:
            day.monthly = dt.utcnow() - timedelta(days=31)

        # Check if claim is available (29-day interval)
        if (day.monthly + timedelta(days=29)) >= dt.utcnow():
            next_claim_time = day.monthly + timedelta(days=29)
            remaining_time = next_claim_time - dt.utcnow()
            days_left, hours_left = remaining_time.days, remaining_time.seconds // 3600
            await ctx.interaction.response.send_message(
                f"⏳ **You can claim your monthly rewards in {days_left} days and {hours_left} hours!**"
            )
            return

        # Assign rewards based on role hierarchy
        rewards = {
            "Nitro": 10000,
            "Initiate": 20000,
            "Acolyte": 30000,
            "Ascended": 40000
        }
        reward = max(rewards[role] for role, role_obj in supporter_roles.items() if role_obj in ctx.author.roles)

        # Update user's coin balance and reset monthly claim
        c.coins += reward
        day.monthly = dt.utcnow()
        async with self.bot.database() as db:
            await c.save(db)
            await day.save(db)

        coin_emoji = self.bot.config['emojis']['coin']
        embed = Embed(
            title="🎉 Monthly Reward Claimed! 🎉",
            description=(
                f"Thank you for supporting us, {ctx.author.mention}! 🌟\n\n"
                f"**You've been rewarded:**\n"
                f"💰 **{reward:,} {coin_emoji}**\n\n"
                "Keep enjoying your exclusive benefits and have a fantastic month ahead!"
            ),
            color=0x00FF00,
            timestamp=dt.utcnow()
        )
        embed.set_footer(text="Exclusive Supporter Reward")

        await ctx.interaction.response.send_message(embed=embed)
        await self.coin_logs.send(f"💸 **{ctx.author}** claimed **{reward:,} {coin_emoji}** as their monthly reward!")


def setup(bot):
    bot.add_cog(Monthly(bot))
