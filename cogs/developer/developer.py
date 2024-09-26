
#* Discord
from discord.ext.commands import command, Cog
from discord import Member, PermissionOverwrite, Permissions

#*Additions
from asyncio import sleep, iscoroutine
from time import monotonic
from datetime import datetime as dt, timedelta
from random import choice
import utils
import os
import sys
import subprocess

from asyncio import iscoroutine, gather
from traceback import format_exc


class Developer(Cog):
    def __init__(self, bot):
        self.bot = bot




    @utils.is_dev()
    @command()
    async def ev(self, ctx, *, content:str):
        """
        Runs code through Python
        """
        try:
            ans = eval(content, globals(), locals())
        except Exception:
            await ctx.send('```py\n' + format_exc() + '```')
            return
        if iscoroutine(ans):
            ans = await ans
        await ctx.send('```py\n' + str(ans) + '```')


    @utils.is_dev()
    @command(aliases=['r'])
    async def restart(self, ctx):
        """Restarts the bot"""
        msg = await ctx.send(embed=utils.Embed(title=f"Restarting..."))
        for num in range(5):
            await sleep(1)
            await msg.edit(embed=utils.Embed(title=f"Restarting in {5-num}."))
        await ctx.message.delete()
        await msg.delete()
        python = sys.executable
        os.execl(python, python, *sys.argv)


    @command()
    async def ping(self, ctx):
        """Checks bot's ping"""
        await sleep(1)
        await ctx.message.delete()
        before = monotonic()
        message = await ctx.send("Pong!")
        ping = (monotonic() - before) * 1000
        users = len(set(self.bot.get_all_members()))
        servers = len(self.bot.guilds)
        await message.edit(embed=utils.Embed(desc=f"Ping:`{int(ping)}ms`\nUsers: `{users}`\nServers: `{servers}`"))



    @utils.is_dev()
    @command()
    async def checklevels(self, ctx):
        for member in ctx.guild.members:
            await utils.UserFunctions.check_level(member)

        await ctx.send('All members have had their level roles adjusted correctly.')

    @utils.is_dev()
    @command()
    async def checkage(self, ctx):
        mod = utils.Moderation.get(ctx.author.id)
        for member in ctx.guild.members:
            for i in member.roles:
                if i.id == self.bot.config['age_roles']['adult']:
                    mod.adult = True
                    mod.child = False
                if i.id == self.bot.config['age_roles']['underage']:
                    mod.adult = False
                    mod.child = True

        await ctx.send('All members age moderation parameters have been set.')


    @utils.is_dev()
    @command()
    async def mass_verify(self, ctx):
        """Verify all users on server"""
        for member in ctx.guild.members:
            await utils.UserFunctions.verify_user(member)
            print(f'{member.name} was verified!')
        await ctx.send('All members have been verified!')





    @utils.is_dev()
    @command()
    async def sm(self, ctx):
        """send a placeholder message"""
        await ctx.message.delete()
        await ctx.send('placeholder message!')





def setup(bot):
    x = Developer(bot)
    bot.add_cog(x)