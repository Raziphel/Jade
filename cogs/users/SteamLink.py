from discord.ext.commands import command, Cog, ApplicationCommandMeta


import utils


class SteamLink(Cog):
    def __init__(self, bot):
        self.bot = bot



    @command(application_command_meta=ApplicationCommandMeta())
    async def steamlink(self, ctx):
        """Links the user's Discord account with their Steam ID if connected."""
        discord_id = ctx.author.id  # Get the Discord user ID from the context
        user = ctx.author  # Get the user object

        # Check user connections
        connections = user.connections  # This will give us a list of connected accounts

        steam_id = None
        for connection in connections:
            if connection.type == 'steam':
                steam_id = connection.id  # Get the Steam ID
                break  # Exit the loop once we find the Steam account

        if steam_id is None:
            await ctx.send("You don't have a Steam account linked to your Discord account.")
            return

        # Create or get the UserLink instance
        user_link = utils.UserLink(discord_id, steam_id)

        async with self.bot.database() as db:
            await user_link.save(db)

        await ctx.send(f"Successfully linked your Discord account with Steam ID: {steam_id}")


def setup(bot):
    bot.add_cog(SteamLink(bot))