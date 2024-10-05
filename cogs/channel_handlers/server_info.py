
from discord import Embed, RawReactionActionEvent
from discord.ext.commands import Cog 

import utils


class server_info(Cog):
    def __init__(self, bot):
        self.bot = bot


    @property  #+ The Server Logs
    def discord_log(self):
        return self.bot.get_channel(self.bot.config['logs']['server']) 


    @Cog.listener()
    async def on_ready(self):
        """Displays the role handler messages"""
        ch = self.bot.get_channel(self.bot.config['channels']['server_info'])

        msg1 = await ch.fetch_message(self.bot.config['server_info_messages']['1'])
        msg2 = await ch.fetch_message(self.bot.config['server_info_messages']['2'])
        msg3 = await ch.fetch_message(self.bot.config['server_info_messages']['3'])

        embed1=Embed(description=f"# SCP Server Info\nIf for some reason the servers are not showing up on the Server List.  You can direct connect to the servers using the command:\n`connect n01.infra.serpents.garden:7777-7780`\n\nYou can also visit our CedMod site by going to `scp.serpents.garden` where can see a list of players online as well as link your discord account for in-game badges and rewards.", color=0xff0000)

        embed2=Embed(description=f"# Discord -> SCP Server linking\nConnecting your discord account to our CedMod integration allows you to be able to receive rewards from the Discord!  It's required if you choose to donate or nitro boost the discord, so that you can get any benefits!\n\n1.) Run this command on the discord `/account link`\n2.) Go through the process of logging in on the link provided.\n3.) **Profit!**", color=0xffff00)

        embed3=Embed(description=f"# Server Plugins\n\nA full list of plugins and there functions will be available when Razi isn't a Lazy bitch....", color=0x0000ff)

        # List of messages and corresponding embeds
        messages_and_embeds = [
            (msg1, embed1),
            (msg2, embed2),
            (msg3, embed3)
        ]

        # Loop through the messages and queue edits
        for message, embed in messages_and_embeds:
            await self.bot.message_edit_manager.queue_edit(
                message=message,
                new_content=" ",
                new_embed=embed
            )


def setup(bot):
    x = server_info(bot)
    bot.add_cog(x)