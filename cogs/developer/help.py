# Discord
from random import randint
from discord import Embed
from discord.ext.commands import command, Cog, Group, ApplicationCommandMeta, Command
import discord

class Help(Cog):
    def __init__(self, bot):
        self.bot = bot

        # Save the original help command and remove it
        self.original_help = bot.get_command('help')
        bot.remove_command('help')

    def cog_unload(self):
        # Restore the original help command when the cog is unloaded
        self.bot.add_command(self.original_help)

    async def cog_command_error(self, ctx, error):
        # Log the error or handle it as needed
        await ctx.send(f"An error occurred: {str(error)}")

    @command(
        name='help',
        aliases=['commands'],
        hidden=True,
        application_command_meta=ApplicationCommandMeta(),
    )
    async def help(self, ctx, *, command_name: str = None):
        """Displays a list of commands or detailed help for a specific command."""

        # If no command is specified, show the general help menu
        if not command_name:
            help_embed = self.generate_general_help(ctx)
        else:
            help_embed = self.generate_command_help(ctx, command_name)

        # Send the embed to the user
        try:
            await ctx.author.send(embed=help_embed)
            if ctx.guild:
                await ctx.send("I've sent you a DM with a list of commands!")
        except discord.Forbidden:
            await ctx.send("I couldn't send you a DM. Please check your privacy settings.")

    def generate_general_help(self, ctx):
        """Generate an embed with the general help information for all available commands."""
        help_embed = Embed(title="Help", description="Here are the available commands:", color=randint(1, 0xffffff))
        help_embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)

        # Fetch all cogs and their commands
        for cog_name, cog in self.bot.cogs.items():
            cog_commands = [command for command in cog.get_commands() if command.hidden is False and command.enabled]
            if not cog_commands:
                continue

            # Add the commands for each cog in the embed
            value = '\n'.join([f"**{ctx.prefix}{command.name}** - {command.short_doc or 'No description'}" for command in cog_commands])
            help_embed.add_field(name=cog_name, value=value, inline=False)

        help_embed.set_footer(text=f"Use {ctx.prefix}help <command> for more details on a specific command.")
        return help_embed

    def generate_command_help(self, ctx, command_name):
        """Generate detailed help for a specific command or command group."""
        command = self.bot
        for part in command_name.split():
            command = command.get_command(part)
            if command is None:
                return Embed(title="Error", description=f"Command `{command_name}` not found.", color=0xff0000)

        # Handle group commands and their subcommands
        if isinstance(command, Group):
            subcommands = command.walk_commands()
            subcommand_list = '\n'.join([f"**{ctx.prefix}{subcommand.qualified_name}** - {subcommand.short_doc or 'No description'}"
                                         for subcommand in subcommands if subcommand.hidden is False and subcommand.enabled])
            help_embed = Embed(
                title=f"Help: {command.qualified_name}",
                description=f"{command.help or 'No description'}\n\n**Subcommands:**\n{subcommand_list}",
                color=randint(1, 0xffffff)
            )
        else:
            help_embed = Embed(
                title=f"Help: {command.qualified_name}",
                description=command.help or "No description available.",
                color=randint(1, 0xffffff)
            )

        help_embed.set_footer(text=f"Command usage: {ctx.prefix}{command.qualified_name}")
        return help_embed


def setup(bot):
    bot.add_cog(Help(bot))
