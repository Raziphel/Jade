# Discord
from discord import ApplicationCommandOption, ApplicationCommandOptionType, Member, Embed, HTTPException
from discord.ext.commands import command, cooldown, BucketType, Cog, ApplicationCommandMeta
import asyncio  # Added to handle the TimeoutError

# Utils
import utils

# Set up game states
games = {}
column_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]


class Connect4(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def coin_logs(self):
        return self.bot.get_channel(self.bot.config['logs']['coins'])

    # Create an empty Connect 4 grid
    def create_grid(self):
        return [["⚪" for _ in range(7)] for _ in range(6)]

    # Create an empty Connect 4 grid with column numbers
    def display_grid(self, grid):
        columns = "1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣\n"
        grid_display = "\n".join(" ".join(row) for row in grid)
        return columns + grid_display

    # Check for a winner (horizontal, vertical, diagonal)
    def check_winner(self, grid, piece):
        # Horizontal
        for row in range(6):
            for col in range(4):
                if all(grid[row][col + i] == piece for i in range(4)):
                    return True
        # Vertical
        for col in range(7):
            for row in range(3):
                if all(grid[row + i][col] == piece for i in range(4)):
                    return True
        # Diagonal (top-left to bottom-right)
        for row in range(3):
            for col in range(4):
                if all(grid[row + i][col + i] == piece for i in range(4)):
                    return True
        # Diagonal (bottom-left to top-right)
        for row in range(3, 6):
            for col in range(4):
                if all(grid[row - i][col + i] == piece for i in range(4)):
                    return True
        return False

    @cooldown(1, 30, BucketType.user)
    @command(
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="opponent",
                    description="The user you want to bet with.",
                    type=ApplicationCommandOptionType.user,
                    required=True,
                ),
                ApplicationCommandOption(
                    name="bet_amount",
                    description="The amount of coins you want to bet.",
                    type=ApplicationCommandOptionType.integer,
                    required=True,
                ),
            ],
        ),
    )
    async def connect4(self, ctx, opponent: Member, bet_amount: int):
        """Gamble over a game of Connect 4!"""
        challenger = ctx.author
        challenger_coins = utils.Currency.get(challenger.id)
        opponent_coins = utils.Currency.get(opponent.id)
        challenger_skills = utils.Skills.get(challenger.id)

        # Check if the user has the skill for Connect 4
        if not challenger_skills.connect4:
            await ctx.send(
                embed=Embed(
                    title="You don't have the skill!",
                    description=f"You must have the Connect 4 skill to challenge someone to Connect 4!",
                    color=0xff0000,
                )
            )
            return
        if challenger == opponent:
            await ctx.send(
                embed=Embed(
                    title="You can't play with yourself!",
                    description=f"That's gross...",
                    color=0xff0000,
                )
            )
            return
        if bet_amount < 100:
            await ctx.send(
                embed=Embed(
                    title="Not betting enough!",
                    description=f"Oh come on, you can bet more than {bet_amount:,} coins!",
                    color=0xff0000,
                )
            )
            return
        if bet_amount > challenger_coins.coins:
            await ctx.send(
                embed=Embed(
                    title="Not enough coins!",
                    description=f"You only have {challenger_coins.coins:,} coins, but you tried to bet {bet_amount:,} coins!",
                    color=0xff0000,
                )
            )
            return
        if bet_amount > opponent_coins.coins:
            await ctx.send(
                embed=Embed(
                    title="Opponent doesn't have enough coins!",
                    description=f"{opponent.mention} doesn't have enough coins to bet {bet_amount:,} coins.",
                    color=0xff0000,
                )
            )
            return

        # Ask the opponent to accept the challenge
        challenge_embed = Embed(
            title="Connect 4 Challenge!",
            description=f"{opponent.mention}, you have been challenged by {challenger.mention} to a Connect 4 game for {bet_amount:,} coins!\n\n"
                        f"React with ✅ to accept or ❌ to decline.",
            color=0x00ff00
        )
        msg = await ctx.send(embed=challenge_embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user == opponent and str(reaction.emoji) in ["✅", "❌"]

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:  # Fixed TimeoutError import
            await ctx.send(
                embed=Embed(
                    title="Game Canceled",
                    description=f"{opponent.mention} did not respond in time! The challenge has been canceled.",
                    color=0xffa500
                )
            )
            return

        if str(reaction.emoji) == "❌":
            await ctx.send(
                embed=Embed(
                    title="Challenge Declined",
                    description=f"{opponent.mention} declined the challenge! The game has been canceled.",
                    color=0xff0000
                )
            )
            return

        # Create a new game
        grid = self.create_grid()
        games[ctx.channel.id] = {
            "grid": grid,
            "players": [challenger.id, opponent.id],
            "turn": challenger.id,  # Challenger starts
            "bet_amount": bet_amount
        }

        # Send the initial game state
        game_embed = Embed(
            title="Connect 4 Game Started!",
            description=f"{challenger.mention} vs {opponent.mention}\nBet: {bet_amount:,} coins\n\n{self.display_grid(grid)}",
            color=0x3498db
        )
        game_message = await ctx.send(embed=game_embed)

        # Add reactions for each column
        for emoji in column_emojis:
            await game_message.add_reaction(emoji)

        # Store the message ID for game reference
        games[ctx.channel.id]["message_id"] = game_message.id

    # In your on_reaction_add for Connect 4
    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        msg_id = reaction.message.id
        channel_id = reaction.message.channel.id

        if channel_id not in games or "message_id" not in games[channel_id] or msg_id != games[channel_id][
            "message_id"]:
            return  # Not an active game or wrong message

        game = games[channel_id]
        grid = game["grid"]

        # Check if it's the player's turn
        if user.id != game["turn"]:
            return  # Not your turn!

        # Cancel the forfeit timer as the player is taking their turn
        if 'forfeit_task' in game and game['forfeit_task']:
            game['forfeit_task'].cancel()

        # Determine the column from the reaction
        if reaction.emoji not in column_emojis:
            return  # Invalid column emoji

        column = column_emojis.index(reaction.emoji)  # Get the column index (0-based)

        # Remove the player's reaction to keep the board clean
        try:
            await reaction.message.remove_reaction(reaction.emoji, user)
        except HTTPException:
            pass  # Fail silently if removing the reaction fails

        # Drop the piece in the selected column
        for row in range(5, -1, -1):
            if grid[row][column] == "⚪":
                grid[row][column] = "🔴" if user.id == game["players"][0] else "🟡"
                break
        else:
            await reaction.message.channel.send("That column is full! Try a different one.")
            return

        # Check for a winner
        piece = "🔴" if user.id == game["players"][0] else "🟡"
        if self.check_winner(grid, piece):
            winner = user
            loser_id = game["players"][1] if user.id == game["players"][0] else game["players"][0]
            loser = self.bot.get_user(loser_id)

            # Pay the winner using the pay_user function
            try:
                await utils.CoinFunctions.pay_user(payer=loser, receiver=winner, amount=game["bet_amount"], bet=True)
                win_embed = Embed(
                    title="Game Over!",
                    description=f"🎉 {winner.mention} wins the game and takes **{game['bet_amount']:,}** coins! 🎉\n\n{self.display_grid(grid)}",
                    color=0x00ff00
                )
                await reaction.message.channel.send(embed=win_embed)

                log_message = f"**Connect 4 Winner**: {winner.name} won **{game['bet_amount']:,}** coins."
                log_channel = self.coin_logs
                if log_channel:
                    await log_channel.send(log_message)

                del games[channel_id]
                return
            except Exception as e:
                await reaction.message.channel.send(
                    embed=Embed(
                        title="Error",
                        description=f"Error occurred when paying the winner: {str(e)}",
                        color=0xff0000
                    )
                )

        # Change turn to the other player
        game["turn"] = game["players"][1] if user.id == game["players"][0] else game["players"][0]
        next_player = self.bot.get_user(game["turn"])

        # Update the grid and prompt the next player
        grid_embed = Embed(
            title="Connect 4 Game",
            description=f"{self.display_grid(grid)}\n\n{next_player.mention}, it's your turn!",
            color=0x3498db
        )
        await reaction.message.edit(embed=grid_embed)

        # Start a 5-minute forfeit timer for the next player
        game['forfeit_task'] = asyncio.create_task(self.forfeit_timer(reaction.message.channel, next_player.id, game))

    # Forfeit timer function
    async def forfeit_timer(self, channel, player_id, game):
        try:
            await asyncio.sleep(300)  # 5 minutes (300 seconds)
            # If we reach here, it means the player took too long
            opponent_id = games[channel.id]["players"][0] if games[channel.id]["turn"] != games[channel.id]["players"][
                0] else games[channel.id]["players"][1]
            opponent = self.bot.get_user(opponent_id)
            forfeiting_player = self.bot.get_user(player_id)

            # Send forfeit message and award the win to the opponent
            await channel.send(
                f"⚠️ {forfeiting_player.mention} took too long and forfeits the game! {opponent.mention} wins **{game['bet_amount']:,}** coins. by "
                f"forfeit.")

            # Handle coins transfer for forfeit
            await utils.CoinFunctions.pay_user(payer=forfeiting_player, receiver=opponent,
                                               amount=games[channel.id]["bet_amount"], bet=True)
            log_message = f"**Tic-Tac-Toe Winner (Forfeit)**: {opponent.name} won **{games[channel.id]['bet_amount']:,}** coins by forfeit."
            log_channel = self.coin_logs
            if log_channel:
                await log_channel.send(log_message)

            del games[channel.id]  # End the game after forfeit
        except asyncio.CancelledError:
            # This will occur if the player moves within the time and the task is canceled
            pass

# Add the cog to the bot
def setup(bot):
    bot.add_cog(Connect4(bot))
