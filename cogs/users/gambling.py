# Discord
from discord import ApplicationCommandOption, ApplicationCommandOptionType, Member
from discord.ext.commands import command, cooldown, BucketType, Cog, ApplicationCommandMeta

# Utils
import utils

# Set up coin tracking and game states
coins = {}
games = {}
column_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]


class Gambling(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def coin_logs(self):
        return self.bot.get_channel(self.bot.config['logs']['coins'])

    # Initialize player coins if not already
    def init_coins(self, user_id):
        if user_id not in coins:
            coins[user_id] = 100  # Default starting coins

    # Create an empty Connect 4 grid
    def create_grid(self):
        return [["⚪" for _ in range(7)] for _ in range(6)]

    # Display the current grid as a string
    def display_grid(self, grid):
        return "\n".join(" ".join(row) for row in grid)

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
        """Gamble over a game of connect 4!"""
        challenger = ctx.author
        self.init_coins(challenger.id)
        self.init_coins(opponent.id)

        if bet_amount > coins[challenger.id]:
            await ctx.send(
                f"You don't have enough coins to bet that amount! You only have {coins[challenger.id]} coins."
            )
            return
        if bet_amount > coins[opponent.id]:
            await ctx.send(f"{opponent.mention} doesn't have enough coins to bet that amount!")
            return

        # Ask the opponent to accept the challenge
        msg = await ctx.send(
            f"{opponent.mention}, you have been challenged by {challenger.mention} to a Connect 4 game for {bet_amount} coins! "
            f"React with ✅ to accept or ❌ to decline."
        )
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user == opponent and str(reaction.emoji) in ["✅", "❌"]

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except TimeoutError:
            await ctx.send(f"{opponent.mention} did not respond in time! The game has been canceled.")
            return

        if str(reaction.emoji) == "❌":
            await ctx.send(f"{opponent.mention} declined the challenge! The game has been canceled.")
            return

        # Proceed with the game if accepted
        coins[challenger.id] -= bet_amount
        coins[opponent.id] -= bet_amount

        # Create a new game
        grid = self.create_grid()
        games[ctx.channel.id] = {
            "grid": grid,
            "players": [challenger.id, opponent.id],
            "turn": challenger.id,  # Challenger starts
            "bet_amount": bet_amount
        }

        # Send the initial game state
        game_message = await ctx.send(
            f"Connect 4 game between {challenger.mention} and {opponent.mention} for {bet_amount} coins!\n\n{self.display_grid(grid)}"
        )

        # Add reactions for each column
        for emoji in column_emojis:
            await game_message.add_reaction(emoji)

        # Store the message ID for game reference
        games[ctx.channel.id]["message_id"] = game_message.id

    # Handle reactions (piece dropping)
    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        msg_id = reaction.message.id
        if reaction.message.channel.id not in games or msg_id != games[reaction.message.channel.id]["message_id"]:
            return  # Not an active game or wrong message

        game = games[reaction.message.channel.id]
        grid = game["grid"]

        # Check if it's the player's turn
        if user.id != game["turn"]:
            return  # Not your turn!

        # Determine the column from the reaction
        if reaction.emoji not in column_emojis:
            return  # Invalid column emoji

        column = column_emojis.index(reaction.emoji)  # Get the column index (0-based)

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
                await utils.CoinFunctions.pay_user(payer=loser, receiver=winner, amount=game["bet_amount"])
                await reaction.message.channel.send(f"{winner.mention} wins the game and takes {game['bet_amount']} coins!\n\n{self.display_grid(grid)}")

                # Log the result to the coin log channel
                log_message = f"**Connect 4 Winner**: {winner.name} won {game['bet_amount']} coins and now has a new balance."
                log_channel = self.coin_logs
                if log_channel:
                    await log_channel.send(log_message)

                del games[reaction.message.channel.id]
                return
            except Exception as e:
                await reaction.message.channel.send(f"Error occurred when paying the winner: {str(e)}")

        # Change turn to the other player
        game["turn"] = game["players"][1] if user.id == game["players"][0] else game["players"][0]
        next_player = self.bot.get_user(game["turn"])

        # Update the grid and prompt the next player
        await reaction.message.edit(content=f"{self.display_grid(grid)}\n\n{next_player.mention}, it's your turn!")


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Gambling(bot))
