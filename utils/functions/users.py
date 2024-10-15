from asyncio import sleep
from math import floor
from random import randint

from discord import Member, TextChannel

import utils


class UserFunctions(object):
    bot = None

    @classmethod
    async def verify_user(cls, user: Member):
        """Brings a user back to life, or to life for the first time!"""
        guild = cls.bot.get_guild(cls.bot.config['guild_id'])

        # Send joining server messages
        log = cls.bot.get_channel(cls.bot.config['channels']['welcome'])
        await log.send(content=f"<@&{cls.bot.config['ping_roles']['welcomer']}> {user.mention}  **Make sure to go to <#{cls.bot.config['channels']['roles']}> to choose what areas of the server you get access to!**", embed=utils.Embed(color=randint(1, 0xffffff), title=f"{user.name} has joined Serpent's Garden."))

        # Assign new member roles
        verified = utils.DiscordGet(guild.roles, id=cls.bot.config['access_roles']['verified'])
        await user.add_roles(verified, reason="Verification")

        # Make sure they have the correct level role
        await cls.check_level(user)

    @classmethod
    async def level_up(cls, user: Member, channel: TextChannel = None):
        """Checks if they should level up and then levels up!"""

        # Set Variables
        msg = None
        lvl = utils.Levels.get(user.id)
        c = utils.Currency.get(user.id)
        coins_record = utils.Coins_Record.get(user.id)  # Retrieve the user's coins record
        coin_e = cls.bot.config['emojis']['coin']

        # Check if they should even level up
        required_exp = await cls.determine_required_exp(lvl.level)
        if lvl.exp < required_exp:
            return

        # Level them up!
        lvl.exp = 0
        lvl.level += 1
        coins = (lvl.level * 250) + 5000


        # Earn coins and update the coins record
        await utils.CoinFunctions.earn(earner=user, amount=coins)
        coins_record.earned += coins  # Track earned coins

        # Save the updated data to the database
        async with cls.bot.database() as db:
            await lvl.save(db)
            await c.save(db)
            await coins_record.save(db)  # Save the updated coins record

        # Check for a role change
        await cls.check_level(user=user)

        # Log it and notify them
        if channel:
            msg = await channel.send(embed=utils.Embed(color=randint(1, 0xffffff), desc=f"🎉 {user.mention} is now level: **{lvl.level:,}**\nGranting them: **{coin_e} {floor(coins):,}x**"))
        else:
            await user.send(embed=utils.Embed(color=randint(1, 0xffffff), desc=f"🎉 You are now level: **{lvl.level:,}**\nGranting you: **{coin_e} {floor(coins):,}x**"))

        log = cls.bot.get_channel(cls.bot.config['logs']['coins'])
        await log.send(f"**<@{user.id}>** leveled up and is now level **{lvl.level:,}**\nGranting them: **{coin_e} {floor(coins):,}x**")

        await sleep(6)
        try:
            await msg.delete()
        except:
            pass

    @classmethod
    async def determine_required_exp(cls, level: int):
        """Determines how much exp is needed to level up!"""
        if level == 0:
            return 10
        elif level < 4:
            return level * 20
        elif level > 100:
            return 500000
        else:
            return round(10 + (level ** 2.1) * 30)

    @classmethod
    async def check_level(cls, user: Member):
        """Checks the highest level role that the given user is able to receive"""

        # Get the guild and user data
        guild = cls.bot.get_guild(cls.bot.config['guild_id'])
        lvl = utils.Levels.get(user.id)

        # Level roles mapping
        level_roles = {
            200: "Level 200",
            195: "Level 195",
            190: "Level 190",
            185: "Level 185",
            180: "Level 180",
            175: "Level 175",
            170: "Level 170",
            165: "Level 165",
            160: "Level 160",
            155: "Level 155",
            150: "Level 150",
            145: "Level 145",
            140: "Level 140",
            135: "Level 135",
            130: "Level 130",
            125: "Level 125",
            120: "Level 120",
            115: "Level 115",
            110: "Level 110",
            105: "Level 105",
            100: "Level 100",
            95: "Level 95",
            90: "Level 90",
            85: "Level 85",
            80: "Level 80",
            75: "Level 75",
            70: "Level 70",
            65: "Level 65",
            60: "Level 60",
            55: "Level 55",
            50: "Level 50",
            45: "Level 45",
            40: "Level 40",
            35: "Level 35",
            30: "Level 30",
            25: "Level 25",
            20: "Level 20",
            15: "Level 15",
            10: "Level 10",
            5: "Level 5",
            0: "Level 0"
        }

        # Determine which role(s) to remove and add
        role_to_delete = [role for role in user.roles if role.name in level_roles.values()]

        viable_level_roles = {i: o for i, o in level_roles.items() if lvl.level >= i}
        role_to_add = viable_level_roles.get(max(viable_level_roles.keys())) if viable_level_roles else None

        # Update roles accordingly
        if role_to_delete:
            await user.remove_roles(*role_to_delete, reason="Removing Level Role.")

        if role_to_add:
            try:
                role = utils.DiscordGet(guild.roles, name=role_to_add)
                await user.add_roles(role, reason="Adding Level Role.")
            except:
                print(f'Failed to apply level role: {user.name} getting role: {role_to_add}')
