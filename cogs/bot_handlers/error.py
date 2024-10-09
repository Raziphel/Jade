#* Discord
from discord.ext.commands import Cog
from discord.ext.commands import BadArgument, CommandNotFound, CommandOnCooldown, MissingPermissions
#* Utils
import utils
#* Additions
from asyncio import sleep


class ErrorHandler(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handles any errors the bot runs into."""

        # Handle command cooldown error
        if isinstance(error, CommandOnCooldown):
            await self.handle_cooldown_error(ctx, error)

        # Ignore if command is not found
        elif isinstance(error, CommandNotFound):
            return

        # Handle missing permissions error
        elif isinstance(error, MissingPermissions):
            await self.send_error_message(ctx, "Ya don't have the right Server Permission!")

        # Handle bad argument error
        elif isinstance(error, BadArgument):
            await self.send_error_message(ctx, "Ya gave Incorrect Command Arguments!?")

        # Handle custom errors
        elif isinstance(error, utils.InDmsCheckError):
            await self.send_error_message(ctx, "This command can only be ran in my DMs!")
        elif isinstance(error, utils.UserCheckError):
            await self.send_error_message(ctx, "Only someone special can run this command!")
        elif isinstance(error, utils.DevCheckError):
            await self.send_error_message(ctx, "Only the Bot Developer can run this command!")
        elif isinstance(error, utils.GuildCheckError):
            await self.send_error_message(ctx, "This isn't the right Discord Server for this command.")
        elif isinstance(error, utils.NSFWCheckError):
            await self.send_error_message(ctx, "An NSFW Error Occurred.")
        elif isinstance(error, utils.ModStaffCheckError):
            await self.send_error_message(ctx, "Only a Moderator can run this command!")
        elif isinstance(error, utils.AdminStaffCheckError):
            await self.send_error_message(ctx, "Only an Administrator can run this command!")

        # Handle unexpected errors
        else:
            await self.send_error_message(ctx, "Something unexpected happened?")

        # If developer is the author, notify them
        if ctx.author.id in self.bot.config['developers'].values():
            await ctx.author.send(f"Command failed - `{error!s}`;")

        # Delete the messages after a delay
        await self.delete_messages_after_delay(ctx)

    async def handle_cooldown_error(self, ctx, error):
        """Handles cooldown error messages."""
        countdown_time = error.retry_after

        if countdown_time <= 60:
            msg = await ctx.send(embed=utils.Embed(desc=f"Command on Cooldown.\nPlease try again in {countdown_time:.2f} seconds!"))
        else:
            minutes, seconds = divmod(countdown_time, 60)
            msg = await ctx.send(embed=utils.Embed(desc=f"Command on Cooldown.\nPlease try again in {int(minutes)} minutes {int(seconds)} seconds!"))

        return msg

    async def send_error_message(self, ctx, message):
        """Helper to send a formatted error message."""
        msg = await ctx.send(embed=utils.Embed(desc=message))
        return msg

    async def delete_messages_after_delay(self, ctx):
        """Deletes the message and command after a short delay."""
        await sleep(4)
        try:
            await ctx.message.delete()
            await ctx.channel.purge(limit=1, check=lambda m: m.author == self.bot.user)
        except Exception:
            pass  # Fail silently

def setup(bot):
    bot.add_cog(ErrorHandler(bot))
