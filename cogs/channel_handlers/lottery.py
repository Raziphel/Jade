import asyncio
from datetime import datetime as dt, timedelta
from random import choice

import discord
from discord import Embed
from discord.ext import commands, tasks

import utils


class LotteryHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lottery_update.start()  # Updates lottery status and ticket options
        self.lottery_runner.start()  # Runs the lottery weekly
        self.lottery_pot_increaser.start()  # Increases the lottery pot every hour
        self.lottery_leaderboard_update.start()  # Updates the leaderboard
        self.previous_winner_message = None
        self.ping_sent = False  # Track whether the ping has been sent for the current draw period
        # Ticket options with emojis and costs
        self.ticket_options = {
            "🍏": (1, 1000),  # 1 ticket for 1000 coins (1000 per ticket)
            "🍎": (5, 4750),  # 5 tickets for 4750 coins (950 per ticket, 5% discount)
            "🍐": (20, 18000),  # 20 tickets for 18000 coins (900 per ticket, 5% discount)
            "🍋": (50, 42750),  # 50 tickets for 42750 coins (855 per ticket, 5% discount)
            "🍇": (100, 81000)  # 100 tickets for 81000 coins (810 per ticket, 5% discount)
        }

    def cog_unload(self):
        self.lottery_update.cancel()
        self.lottery_runner.cancel()
        self.lottery_pot_increaser.cancel()
        self.lottery_leaderboard_update.cancel()

    @tasks.loop(minutes=1)
    async def lottery_update(self):
        """Updates the lottery message every minute with the latest stats."""
        await self.bot.wait_until_ready()

        # Fetch lottery data and channel
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = guild.get_channel(self.bot.config['channels']['lottery'])
        lottery = utils.Lottery.get(1)

        # Fetch the message to be updated
        msg = await channel.fetch_message(self.bot.config['lottery_messages']['1'])


        # Calculate time remaining for the lottery
        if lottery.lot_time is not None:
            time_remaining = (lottery.lot_time + timedelta(days=7)) - dt.now()
            if time_remaining.total_seconds() > 0:
                time_remaining_str = str(time_remaining).split('.')[0]  # Format time without milliseconds
            else:
                time_remaining_str = "Lottery ended. Drawing soon..."
        else:
            time_remaining_str = "Lottery not started yet."

        # Build the embed with ticket information, prize pool, and timer
        description = (
            "🎉 **Welcome to the Weekly Lottery!** 🎉\n\n"
            "💰 **Prize Pool:**\n"
            f"```css\n{lottery.coins:,} coins\n```\n"
            "⏳ **Time Until Draw:**\n"
            f"```css\n{time_remaining_str}\n```\n"
            "**The more tickets you buy, the better your odds of winning!**\n\n"
            "Click 🍪 to get updates!"
        )

        embed = Embed(
            title="🎟️ Lottery Information 🎟️",
            description=description,
            color=discord.Color.purple()  # Use a more vibrant color for the embed
        )

        # Add ticket options to the embed
        embed.add_field(
            name="🎫 **Ticket Options:**",
            value="\n".join(
                [f"{emoji} - **{tickets} Tickets**\nCost: {cost:,} {self.bot.config['emojis']['coin']} coins"
                 for emoji, (tickets, cost) in self.ticket_options.items()]),
            inline=False
        )

        # Edit the message with updated content
        await self.bot.message_edit_manager.queue_edit(
            message=msg,
            new_content=f" ",
            new_embed=embed
        )

        # Call manage reactions to maintain the reactions on the lottery message
        await self.manage_reactions(msg)

    @tasks.loop(minutes=10)
    async def lottery_leaderboard_update(self):
        """Updates the lottery leaderboard message every 10 minutes."""
        await self.bot.wait_until_ready()

        # Fetch the necessary Discord objects
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = guild.get_channel(self.bot.config['channels']['lottery'])

        # Fetch the leaderboard message
        msg = await channel.fetch_message(self.bot.config['lottery_messages']['2'])

        # Get the top 10 users with the most tickets using the sort_tickets method, filter out users with zero tickets
        sorted_users = [user for user in utils.Currency.sort_tickets()[:10] if user.tickets > 0]

        # Calculate the total number of tickets for the chance calculation
        total_tickets = sum(user.tickets for user in sorted_users)

        # Build the leaderboard embed
        embed = Embed(
            title="🎟️ Lottery Leaderboard",
            description="Top 10 users with the most tickets and their chances of winning:",
            color=0xffd700
        )

        if not sorted_users:
            embed.add_field(name="No tickets yet!", value="Be the first to buy some tickets!", inline=False)
        else:
            # Create a leaderboard list with winning chances
            leaderboard_text = ""
            for idx, user in enumerate(sorted_users, 1):
                discord_user = await self.bot.fetch_user(user.user_id)
                win_chance = (user.tickets / total_tickets) * 100 if total_tickets > 0 else 0
                leaderboard_text += (
                    f"**#{idx}** "
                    f"{discord_user.display_name:<20} "  # Align the display name to the left with a width of 20
                    f"| 🎟 {user.tickets:>5,} "  # Align the ticket count to the right with commas for thousands
                    f"| 🏆 {win_chance:>6.2f}%\n"  # Align the chance to win to the right with two decimal places
                )

            embed.description += f"\n{leaderboard_text}"

        await self.bot.message_edit_manager.queue_edit(
            message=msg,
            new_content=f" ",
            new_embed=embed
        )

    @tasks.loop(hours=2)
    async def lottery_pot_increaser(self):
        """Increases the lottery pot every hour."""
        await self.bot.wait_until_ready()

        lottery = utils.Lottery.get(1)
        lottery.coins += 250  # Add a fixed amount to the pot every hour

        # Save the updated lottery pot to the database
        async with self.bot.database() as db:
            await lottery.save(db)

    @tasks.loop(minutes=1)
    async def lottery_runner(self):
        """Runs the lottery every week and announces the winner."""
        await self.bot.wait_until_ready()

        lottery = utils.Lottery.get(1)
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = guild.get_channel(self.bot.config['channels']['lottery'])

        # Check if the lottery time has been set
        if lottery.lot_time is None:
            return  # Skip processing if the lottery hasn't started yet

        # Calculate time remaining for the lottery
        time_remaining = (lottery.lot_time + timedelta(days=7)) - dt.now()

        # Check if it's 1 hour before the draw and send a ping to the lottery ping role
        if timedelta(hours=0) < time_remaining <= timedelta(hours=1) and not self.ping_sent:
            # Fetch the lottery ping role
            lottery_ping_role = guild.get_role(self.bot.config['lottery_roles']['ping'])

            # Send a reminder message and ping the role
            await channel.send(
                f"{lottery_ping_role.mention} ⏳ The lottery draw will take place in 1 hour! Get your tickets now!")
            self.ping_sent = True


        # Check if it's time to run the lottery
        if time_remaining <= timedelta(0):
            # Remove the previous winner message if it exists
            if self.previous_winner_message:
                try:
                    msg = await channel.fetch_message(lottery.last_msg_id)
                    await msg.delete()
                except discord.NotFound:
                    pass  # Message was already deleted or not found

            lottery.lot_time = dt.now()

            # Get total tickets and participants
            total_tickets = utils.Currency.get_total_tickets()
            sorted_users = [user for user in utils.Currency.sort_tickets() if user.tickets > 0]

            if total_tickets == 0:
                await channel.send(embed=Embed(description="No one entered the lottery this week. No winner."))
                return

            # Collect all tickets into a list for the draw
            all_tickets = []
            for user in sorted_users:
                all_tickets.extend([user.user_id] * user.tickets)

            # Select a winner
            winner_id = choice(all_tickets)
            winner = guild.get_member(winner_id)

            # Calculate winner's chance of winning
            winner_info = next(user for user in sorted_users if user.user_id == winner_id)
            win_chance = (winner_info.tickets / total_tickets) * 100

            # Announce the winner with additional details
            winner_message = await channel.send(embed=Embed(
                title="🎉 **Lottery Winner Announcement** 🎉",
                description=(
                    f"**🥳 Congratulations! The winner of this week's lottery is:**\n\n"
                    f"💎 **{winner.display_name}** 💎\n\n"
                    f"🎟️ **Lottery Stats:**\n"
                    f"```yaml\n"
                    f"- Total Tickets Purchased: {total_tickets}\n"
                    f"- Total Participants: {len(sorted_users)}\n"
                    f"- {winner.display_name}'s Tickets: {winner_info.tickets:,}\n"
                    f"- Winning Chance: {win_chance:.2f}%\n"
                    f"- Prize Amount: {lottery.coins:,} Coins\n"
                    f"```\n"
                    f"💰 **Enjoy your prize!** 💰"
                ),
                color=discord.Color.gold()
            ))

            # Give him winner role and remove last winner role
            winner_role = utils.DiscordGet(guild.roles, id=self.bot.config['lottery_roles']['winner'])
            await winner.add_roles(winner_role, reason="Won the lottery.")
            for member in guild.members:
                if winner_role in member.roles:
                    await member.send("# You are no longer restricted from participating in the lottery.")
                    await member.remove_roles(winner_role, reason="Been a week since last win.")
                    return

            # Distribute the prize
            winner_currency = utils.Currency.get(winner.id)
            winner_record = utils.Coins_Record.get(winner.id)
            winnings = utils.CoinFunctions.pay_tax(payer=winner, amount=lottery.coins)
            winner_currency.coins += winnings
            winner_record.won += winnings

            # Reset lottery
            lottery.last_winner_id = winner.id
            lottery.last_amount = lottery.coins
            lottery.coins = 0
            lottery.last_msg_id = winner_message.id  # Store the winner message for later removal


            # Save changes to the database
            async with self.bot.database() as db:
                await lottery.save(db)
                await winner_currency.save(db)
                await winner_record.save(db)

            # Reset everyone's tickets
            for member in guild.members:
                c = utils.Currency.get(member.id)
                c.lot_tickets = 0
                async with self.bot.database() as db:
                    await c.save(db)


    @commands.Cog.listener('on_raw_reaction_add')
    async def lot_buy(self, payload):
        """Handles lottery ticket purchases based on reactions."""
        if payload.channel_id != self.bot.config['channels']['lottery']:  # Lottery channel
            return

        # Ensure the user is not a bot
        if self.bot.get_user(payload.user_id).bot:
            return

        # Fetch user, lottery, and roles
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        currency = utils.Currency.get(member.id)
        lottery = utils.Lottery.get(1)

        # Restriction check for lottery participation
        role_restricted = utils.DiscordGet(guild.roles, id=self.bot.config['lottery_roles']['winner'])
        if role_restricted in member.roles:
            await member.send("You are restricted from participating in the lottery.")
            return

        emoji = str(payload.emoji)

        if emoji == "🍪":
            updates_role = utils.DiscordGet(guild.roles, id=self.bot.config['lottery_roles']['ping'])
            if updates_role not in member.roles:
                await member.add_roles(updates_role, reason="Subscribed to lottery updates.")
                await member.send("You have subscribed to lottery updates.")
            else:
                await member.remove_roles(updates_role, reason="Unsubscribed from lottery updates.")
                await member.send("You have unsubscribed from lottery updates.")
            return

        # Process ticket purchase based on emoji reaction
        if emoji in self.ticket_options:
            tickets, cost = self.ticket_options[emoji]

            # Send confirmation message
            confirm_embed = Embed(
                title="Confirm Your Lottery Ticket Purchase",
                description=(
                    f"Are you sure you want to purchase {tickets} tickets for {cost:,} {self.bot.config['emojis']['coin']} coins?\n"
                    f"React with ✅ to confirm or ❌ to cancel."
                ),
                color=discord.Color.blue()
            )

            confirmation_msg = await member.send(embed=confirm_embed)

            # Add confirmation and cancellation reactions
            await confirmation_msg.add_reaction("✅")
            await confirmation_msg.add_reaction("❌")

            def check(reaction, user):
                return user == member and str(reaction.emoji) in ["✅",
                                                                  "❌"] and reaction.message.id == confirmation_msg.id

            try:
                # Wait for user to confirm or cancel purchase
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "✅":
                    # Use CoinFunctions to handle the purchase
                    if await utils.CoinFunctions.pay_for(payer=member, amount=cost):
                        # Add tickets to user and update lottery stats
                        currency.tickets += tickets
                        lottery.coins += cost

                        # Confirmation via DM with details of the purchase
                        embed = Embed(
                            title="Lottery Ticket Purchase Confirmation",
                            description=f"You have successfully purchased {tickets} tickets for {cost:,} {self.bot.config['emojis']['coin']} coins!",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Current Tickets", value=f"{currency.tickets} tickets", inline=False)
                        embed.add_field(name=f"Remaining Coins",
                                        value=f"{currency.coins:,} coins", inline=False)

                        await member.send(embed=embed)

                        # Save updates to the database
                        async with self.bot.database() as db:
                            await currency.save(db)
                            await lottery.save(db)

                    else:
                        # Send message if the user does not have enough coins
                        await member.send("You do not have enough coins to purchase tickets.")

                else:
                    # Send cancellation message if user chose to cancel
                    await member.send("Your lottery ticket purchase has been canceled.")

            except asyncio.TimeoutError:
                # Handle timeout, assume purchase is canceled if no response within the time limit
                await member.send("You took too long to respond. Your lottery ticket purchase has been canceled.")

            finally:
                # Clean up the confirmation message to remove reactions
                try:
                    await confirmation_msg.delete()
                except discord.NotFound:
                    pass  # Message was already deleted

        # Call manage reactions to maintain the reactions on the lottery message
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await self.manage_reactions(message)

    async def manage_reactions(self, message):
        """Handle message reactions cleanup and re-adding of correct reactions."""
        # Maximum reaction threshold before clearing all reactions
        max_reactions = 100
        current_reactions = sum(reaction.count for reaction in message.reactions)

        if current_reactions > max_reactions:
            await message.clear_reactions()

            # Add back the appropriate reactions
            ticket_options = ["🍪", "🍏", "🍎", "🍐", "🍋", "🍇"]
            for emoji in ticket_options:
                await message.add_reaction(emoji)


def setup(bot):
    bot.add_cog(LotteryHandler(bot))
