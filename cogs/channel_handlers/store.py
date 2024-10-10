# * Discord
from discord import RawReactionActionEvent, Embed
from discord.ext.commands import Cog
from math import floor
import utils


class StoreHandler(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property  # ! The currency logs
    def coin_logs(self):
        return self.bot.get_channel(self.bot.config['logs']['coins'])

    @Cog.listener('on_ready')
    async def store_msg(self):
        ch = self.bot.get_channel(self.bot.config['channels']['store'])
        store_messages = self.bot.config['store_messages']

        # Fetch and update messages
        messages = [await ch.fetch_message(store_messages[str(i)]) for i in range(1, 7)]
        embeds = [
            Embed(
                description="# Garden Specials\n`All the listed items are worth real life money for the cost of gems!`",
                color=0xFF0000)
            .add_field(name="⊰ ✨ Discord Nitro ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}10,000,000x**\n\n```Get the 10$ Discord Nitro!```",
                       inline=True)
            .add_field(name="⊰ 💸 Get 5$USD! ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}5,000,000x**\n\n```Turn your coins into $USD!```",
                       inline=True),
            Embed(description="# Permissions\n`All these listed items give you general permissions on the server!`",
                  color=0x00FF00)
            .add_field(name="⊰ 📚 Library Pass ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}150,000x**\n\n```Get access to all of the "
                             f"server's logs!```",
                       inline=True)
            .add_field(name="⊰ 🎫 Image Pass ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}150,000x**\n\n```Get permission for images & "
                             f"embeds in General Chats.```",
                       inline=True)
            .add_field(name="⊰ 🔊 SoundBoard Pass ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}150,000x**\n\n```Get access to using the "
                             f"soundboard in VC!```",
                       inline=True)
            .add_field(name="⊰ 🎁 Stats Channel ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}75,000x**\n\n```Get permission to the Stats Channels!```",
                       inline=True)
            .add_field(name="⊰ 🧶 Thread Perms ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}75,000x**\n\n```Get perms to create threads!```",
                       inline=True)
            .add_field(name="⊰ 🔮 External Emotes ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}75,000x**\n\n```Get access to using your external emotes and stickers!```",
                       inline=True),
            Embed(
                description="# Abilities\n`All these listed items give you the ability to do something here in the garden!`",
                color=0xFF00FF)
            .add_field(name="⊰ 🧤 Thievery ⊱",
                       value=f"**╰⊰ {self.bot.config['emojis']['coin']}250,000x**\n\n```Gain the ability to steal from others!```",
                       inline=True)
            .add_field(name="⊰ 4️⃣ Connect 4 ⊱",
                   value=f"**╰⊰ {self.bot.config['emojis']['coin']}250,000x**\n\n```Gain the ability to Challenge others to Connect 4!```",
                   inline=True)
            .add_field(name="⊰ 📦 TicTacToe ⊱",
                   value=f"**╰⊰ {self.bot.config['emojis']['coin']}250,000x**\n\n```Gain the ability to Challenge others to TicTacToe!```",
                   inline=True),

            Embed(
                description="# Colors\n`All these listed items let you be the colors you wanna be!\nDon't waste your "
                            "coins staff, donators and nitro boosters!  These will not work!`",
                color=0x0000FF)
            .add_field(name="⊰ 🍑 Cutie Pinkie ⊱",
                       value=f"<@&{self.bot.config['purchase_roles']['cutie_pinkie']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}1,000,000x**",
                       inline=True)
            .add_field(name="⊰ ⛅ Snow Flakes ⊱",
                       value=f"<@&{self.bot.config['purchase_roles']['snow_flakes']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}1,000,000x**",
                       inline=True)
            .add_field(name="⊰ 🖤 Black Knight ⊱",
                       value=f"<@&{self.bot.config['purchase_roles']['black_knight']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}1,000,000x**",
                       inline=True)
            .add_field(name="⊰ 🍏 Nature Green ⊱",
                       value=f"<@&{self.bot.config['purchase_roles']['nature_green']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}100,000x**",
                       inline=True)
            .add_field(name="⊰ 🧊 Liquid Blue ⊱",
                       value=f"<@&{self.bot.config['purchase_roles']['liquid_blue']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}100,000x**",
                       inline=True)
            .add_field(name="⊰ 🌞 Sunshine Yellow ⊱",
                       value=f"<@&{self.bot.config['purchase_roles']['sunshine_yellow']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}100,000x**",
                       inline=True)
            .add_field(name="⊰ 🌋 Lava Red ⊱",
                       value=f"{self.bot.config['purchase_roles']['lava_red']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}100,000x**",
                       inline=True)
            .add_field(name="⊰ 🧙‍♂️ Magic Purple ⊱",
                       value=f"<@&{self.bot.config['purchase_roles']['magic_purple']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}100,000x**",
                       inline=True)
            .add_field(name="⊰ ☔ Lush Magenta ⊱",
                       value=f"<@&{self.bot.config['purchase_roles']['lush_magenta']}>\n**╰⊰"
                             f" {self.bot.config['emojis']['coin']}100,000x**",
                       inline=True)
        ]

        # Compact loop to handle both cases
        for i, msg in enumerate(messages):
            if i < 4:
                # Queue the first three messages with corresponding embeds
                await self.bot.message_edit_manager.queue_edit(
                    message=msg,
                    new_content=" ",
                    new_embed=embeds[i]  # Access corresponding embed by index
                )
            else:
                # Queue the remaining messages with only content
                await self.bot.message_edit_manager.queue_edit(
                    message=msg,
                    new_content="~",
                    new_embed=None  # No embed for these messages
                )

    @Cog.listener('on_raw_reaction_add')
    async def store_buy(self, payload: RawReactionActionEvent):
        """Buys items from the store based on reactions."""
        # Ensure it's the store channel and bot is connected
        if payload.channel_id != self.bot.config['channels']['store'] or not self.bot.connected:
            return

        user = self.bot.get_user(payload.user_id)
        if user.bot:
            return

        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        # Shop items and their prices
        shop_items = {
            # Real World
            "✨": {"name": "Discord Nitro", "price": 10000000, "role": None},
            "💸": {"name": "5$USD", "price": 5000000, "role": None},
            # Permissions
            "📚": {"name": "Library Pass", "price": 150000, "role": 'library_pass'},
            "🎫": {"name": "Image Pass", "price": 150000, "role": 'image_pass'},
            "🔊": {"name": "Soundboard Pass", "price": 150000, "role": 'soundboard_pass'},
            "🎁": {"name": "Stats Channel", "price": 75000, "role": 'stats_channel_access'},
            "🧶": {"name": "Thread Permissions", "price": 75000, "role": 'threads_perm'},
            "🔮": {"name": "External Emojis", "price": 75000, "role": 'external_emojis'},
            # Abilities
            "🧤": {"name": "Thievery", "price": 250000, "role": None, "ability": "thievery"},
            "4️⃣": {"name": "Connect 4", "price": 250000, "role": None, "ability": "connect4"},
            "📦": {"name": "TicTacToe", "price": 250000, "role": None, "ability": "tictactoe"},
            #role Colors
            "🍑": {"name": "Cutie Pinkie", "price": 1000000, "role": 'cutie_pinkie'},
            "⛅": {"name": "Snow Flakes", "price": 1000000, "role": 'snow_flakes'},
            "🖤": {"name": "Black Knight", "price": 1000000, "role": 'black_knight'},
            "🍏": {"name": "Nature Green", "price": 100000, "role": 'nature_green'},
            "🧊": {"name": "Liquid Blue", "price": 100000, "role": 'liquid_blue'},
            "🌞": {"name": "Sunshine Yellow", "price": 100000, "role": 'sunshine_yellow'},
            "🌋": {"name": "Lava Red", "price": 100000, "role": 'lava_red'},
            "🧙‍♂️": {"name": "Magic Purple", "price": 100000, "role": 'magic_purple'},
            "☔": {"name": "Lush Magenta", "price": 100000, "role": 'lush_magenta'},
        }

        emoji = payload.emoji.name if payload.emoji.is_unicode_emoji() else payload.emoji.id
        if emoji not in shop_items:
            return

        item = shop_items[emoji]
        confirmation_msg = await user.send(embed=utils.Embed(user=user,
                                                             desc=f"# Purchase Confirmation:\nWould you like to buy {item['name']} for {item['price']} {self.bot.config['emojis']['coin']}x?"))

        if await self.purchasing(confirmation_msg, payload, item):
            # Handle the successful purchase
            if item.get("role"):
                role = utils.DiscordGet(guild.roles, id=self.bot.config['purchase_roles'][item["role"]])
                await user.add_roles(role, reason=f"Given {item['name']} role.")

            if item.get("ability"):
                setattr(utils.Skills.get(user.id), item["ability"], True)

            # Send confirmation with remaining coins
            user_currency = utils.Currency.get(user.id)
            embed = Embed(
                title="Purchase Successful",
                description=f"You have successfully bought **{item['name']}** for **{item['price']:,} {self.bot.config['emojis']['coin']}x**!",
                color=0x339c2a
            )
            embed.add_field(name="Remaining Coins", value=f"{user_currency.coins:,} {self.bot.config['emojis']['coin']}x", inline=False)
            await user.send(embed=embed)

            # Log the transaction
            await self.coin_logs.send(f"# {user} bought {item['name']}!")

        else:
            await self.coin_logs.send(f"# {user} tried to purchase: {item['name']}!")

        # Manage message reactions
        await self.manage_reactions(payload)



    async def manage_reactions(self, payload):
        """Handle message reactions cleanup."""
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if sum(reaction.count for reaction in message.reactions) > 100:
            await message.clear_reactions()
        for reaction in message.reactions:
            await message.add_reaction(reaction.emoji)

    async def purchasing(self, msg, payload, item):
        """Handles the purchase confirmation and processing."""
        user = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)

        await msg.add_reaction("✔")
        await msg.add_reaction("❌")

        try:
            check = lambda r, u: u.id == user.id and r.message.id == msg.id and str(r.emoji) in ["✔", "❌"]
            reaction, _ = await self.bot.wait_for('reaction_add', check=check)

            if str(reaction.emoji) == "✔":
                # Attempt the transaction
                if not await utils.CoinFunctions.pay_for(payer=user, amount=item["price"]):
                    await msg.edit(embed=utils.Embed(color=0xc74822,
                                                     desc=f"# You don't have enough coins {self.bot.config['emojis']['coin']}!"))
                    return False
                return True

            if str(reaction.emoji) == "❌":
                await msg.edit(embed=utils.Embed(color=0xc74822, desc="Purchase was canceled!"))
                return False

        except TimeoutError:
            await msg.edit(content='# Sorry, you took too long to respond. Transaction Canceled.', embed=None)
            return False



def setup(bot):
    bot.add_cog(StoreHandler(bot))
