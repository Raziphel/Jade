# Discord
from discord import ApplicationCommandOption, ApplicationCommandOptionType, Member, Embed
from discord.ext.commands import command, cooldown, BucketType, Cog, ApplicationCommandMeta

# Utils
import utils
from math import floor


class Payment(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def coin_logs(self):
        """Returns the coin logs channel."""
        return self.bot.get_channel(self.bot.config['channels']['coin_logs'])

    @cooldown(1, 30, BucketType.user)
    @command(
        aliases=['send'],
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="recipient",
                    description="The user you want to send coins to.",
                    type=ApplicationCommandOptionType.user,
                    required=True,
                ),
                ApplicationCommandOption(
                    name="amount",
                    description="The amount of coins you'd like to send.",
                    type=ApplicationCommandOptionType.integer,
                    required=True,
                ),
            ],
        ),
    )
    async def pay(self, ctx, recipient: Member = None, amount: int = 0):
        """Send coins to another member (With a tax)."""
        coin_emoji = self.bot.config['emojis']['coin']

        # Check if the recipient is valid
        if recipient == ctx.author:
            return await ctx.interaction.response.send_message(
                embed=Embed(
                    title="Invalid Action!",
                    description="You can't send coins to yourself! 🤦‍♂️",
                    color=0xffcc00
                )
            )

        # Ensure the amount is valid
        if amount <= 1000:
            return await ctx.interaction.response.send_message(
                embed=Embed(
                    title="Invalid Amount!",
                    description="The amount must be more than 1,000 coins.",
                    color=0xffcc00
                )
            )

        # Get user's currency and check if they have enough coins (after taxes)
        user_currency = utils.Currency.get(ctx.author.id)
        if amount > (user_currency.coins - amount * utils.CoinFunctions.tax_rate):
            return await ctx.interaction.response.send_message(
                embed=Embed(
                    title="Insufficient Coins!",
                    description=f"You don't have enough coins to send this amount (considering taxes).",
                    color=0xff0000
                )
            )

        # Process the payment and calculate tax
        tax = await utils.CoinFunctions.pay_user(payer=ctx.author, receiver=recipient, amount=amount)
        net_amount = floor(amount)
        tax_amount = floor(tax)

        # Create a beautiful embed for success message
        embed = Embed(
            title="Payment Successful!",
            description=f"**{ctx.author.display_name}** has sent **{coin_emoji} {net_amount:,} coins** to **{recipient.display_name}**!",
            color=0x00cc66
        )
        embed.add_field(name="Taxes", value=f"{coin_emoji} {tax_amount:,} coins", inline=False)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        embed.set_footer(text=f"Transaction completed by {ctx.author.display_name}")

        # Send the response embed
        await ctx.interaction.response.send_message(embed=embed)

        # Log the transaction in the coin logs channel
        log_embed = Embed(
            title="Transaction Logged",
            description=f"**{ctx.author.display_name}** sent **{coin_emoji} {net_amount:,} coins** to **{recipient.display_name}**.",
            color=0x00cc66
        )
        log_embed.add_field(name="Tax Collected", value=f"{coin_emoji} {tax_amount:,} coins")
        await self.coin_logs.send(embed=log_embed)


def setup(bot):
    bot.add_cog(Payment(bot))
