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

        embed1 = Embed(
            description=(
                "# 🌍 Modded Minecraft Server Info\n"
                "Welcome to **Serpent's Garden* — our chaotic blend of tech, magic, and absolute madness.\n\n"
                "**IP:** `mc.serpents.garden`\n"
                "**Version:** 1.20.1 (Forge)\n"
                "**Modpack:** Available on CurseForge — search **Serpent's Garden**!\n"
            ),
            color=0xff0000
        )

        embed2 = Embed(
            description=(
                "# 💤 More servers coming soon?\n"
            ),
            color=0xffff00
        )

        embed3 = Embed(
            description=(
                "# 💤 More servers coming soon?\n"
            ),
            color=0x0000ff
        )

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
