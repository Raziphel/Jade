# Discord
from asyncio import sleep
from math import floor
from random import randint

from discord import Member, TextChannel

import utils


class UserFunctions(object):
    bot = None





    @classmethod
    async def verify_user(cls, user:Member):
        """Brings a user back to life, or to life for the first time!"""

        guild = cls.bot.get_guild(cls.bot.config['guild_id'])

        #+ Send joining server messages!
        log = cls.bot.get_channel(cls.bot.config['channels']['welcome'])
        await log.send(content=f"<@&{cls.bot.config['ping_roles']['welcomer']}> {user.mention}  **Make sure to go to <#{cls.bot.config['channels']['roles']}> to choose what areas of the server you get access to!**", embed=utils.Embed(color=randint(1, 0xffffff), title=f"{user.name} has joined Serpent's Garden."))


        #? Assign new member roles.
        verified = utils.DiscordGet(guild.roles, id=cls.bot.config['access_roles']['verified'])
        await user.add_roles(verified, reason="Verification")

        #* Makes sure they get have the correct level role.
        await cls.check_level(user)





    @classmethod
    async def level_up(cls, user:Member, channel:TextChannel=None):
        """Checks if they should level up and then levels up!"""

        #? Set Variables
        msg = None
        lvl = utils.Levels.get(user.id)
        c = utils.Currency.get(user.id)
        coin_e = cls.bot.config['emojis']['coin']

        #? Check if they should even level up!
        required_exp = await cls.determine_required_exp(lvl.level)
        if lvl.exp < required_exp:
            return

        #+ Level em the hell up!
        lvl.exp = 0
        lvl.level += 1
        coins = (lvl.level*1000)

        await utils.CoinFunctions.earn(earner=user, amount=coins)

        async with cls.bot.database() as db:
            await lvl.save(db)
            await c.save(db)

        #? Check for a role change.
        await cls.check_level(user=user)

        #? Log it and tell em.
        if channel:
            msg = await channel.send(embed=utils.Embed(color = randint(1, 0xffffff), desc=f"🎉 {user.mention} is now level: **{lvl.level:,}**\nGranting them: **{coin_e} {floor(coins):,}x**"))
        else:
            await user.send(embed=utils.Embed(color = randint(1, 0xffffff), desc=f"🎉 You are now level: **{lvl.level:,}**\nGranting you: **{coin_e} {floor(coins):,}x**"))

        log = cls.bot.get_channel(cls.bot.config['logs']['coins'])
        await log.send(f"**<@{user.id}>** leveled up and is now level **{lvl.level:,}**\nGranting them: **{coin_e} {floor(coins):,}x**")

        await sleep(6)
        try: await msg.delete()
        except: pass



    @classmethod
    async def determine_required_exp(cls, level:int):
        """Determines how much exp is needed to level up!"""
        if level == 0:
            return 10
        elif level < 4:
            return level * 20
        else:
            # Adjust the formula to scale more smoothly to higher levels
            return round(10 + (level ** 2.1) * 30)


    @classmethod
    async def check_level(cls, user:Member):
        """Checks the highest level role that the given user is able to receive"""

        # Get the users
        guild = cls.bot.get_guild(cls.bot.config['guild_id'])
        lvl = utils.Levels.get(user.id)

        level_roles = {
            90: "Level 90",
            80: "Level 80",
            70: "Level 70",
            60: "Level 60",
            50: "Level 50",
            40: "Level 40",
            30: "Level 30",
            20: "Level 20",
            10: "Level 10",
            0: "Level 0"
        }

        # Get roles from the user we'd need to delete
        try:
            role_to_delete = [i for i in user.roles if i.name in level_roles.values()]
        except IndexError:
            role_to_delete = None

        # Get role that the user is viable to have
        viable_level_roles = {i:o for i, o in level_roles.items() if lvl.level >= i}
        if viable_level_roles:
            role_to_add = viable_level_roles[max(viable_level_roles.keys())]
        else:
            role_to_add = None

        # Add the roles
        if role_to_delete:
            await user.remove_roles(*role_to_delete, reason="Removing Level Role.")

        if role_to_add:
            try:
                role = utils.DiscordGet(guild.roles, name=role_to_add)
                await user.add_roles(role, reason="Adding Level Role.")
            except: 
                print(f'Failed to apply level role: {user.name} getting role: {role_to_add}')