import toml
import logging

from discord.ext import commands
from discord import AllowedMentions

import utils
from utils.database import DatabaseConnection


#+ ------------------------- Serpent Main Class
class Serpent(commands.AutoShardedBot):
    def __init__(self, config: str, secret: str, *args, logger: logging.Logger = None, **kwargs):
        super().__init__(*args, fetch_offline_members=True, guild_subscriptions=True, allowed_mentions = AllowedMentions(roles=True, users=True, everyone=True), **kwargs)

        self.logger = logger or logging.getLogger("Serpent")
        self.config = config
        self.secret = secret


        with open(self.config) as z:
            self.config = toml.load(z)

        with open(self.secret) as z:
            self.secret = toml.load(z)

        #+ Load Utils
        utils.Embed.bot = self
        utils.CoinFunctions.bot = self
        utils.UserFunctions.bot = self

        self.database = DatabaseConnection
        self.database.config = self.secret['database']
        self.startup_method = None
        self.connected = False

    def run(self):
        self.startup_method = self.loop.create_task(self.startup())
        super().run(self.secret['token'])

    async def startup(self):
        """Load database"""
        try:  #? Try this to prevent resetting the database on accident!
            #! Clear cache
            utils.Moderation.all_moderation.clear()
            utils.Levels.all_levels.clear()
            utils.Currency.all_currency.clear()
            utils.Coins_Record.all_coins_record.clear()
            utils.Tracking.all_tracking.clear()
            utils.Daily.all_dailys.clear()
            utils.Skills.all_skills.clear()


            #! Collect from Database
            async with self.database() as db:
                moderation = await db('SELECT * FROM moderation')
                levels = await db('SELECT * FROM levels')
                currency = await db('SELECT * FROM currency')
                coins_record = await db('SELECT * FROM coins_record')
                tracking = await db('SELECT * FROM tracking')
                daily = await db('SELECT * FROM daily')
                skills = await db('SELECT * FROM skills')


            #! Cache all into local objects
            for i in moderation:
                utils.Moderation(**i)
            for i in levels:
                utils.Levels(**i)
            for i in currency:
                utils.Currency(**i)
            for i in coins_record:
                utils.Coins_Record(**i)
            for i in tracking:
                utils.Tracking(**i)
            for i in daily:
                utils.Daily(**i)
            for i in skills:
                utils.Skills(**i)

        except Exception as e:
            print(f"Couldn't connect to the database... :: {e}")

        #! If Razi ain't got levels the DB ain't connected correctly... lmfao
        lvl = utils.Levels.get(159516156728836097)
        if lvl.level == 0:
            self.connected = False
            print('Bot database is NOT connected!')
        else:
            self.connected = True
            print('Bot database is connected!')

        #+ Register slash commands
        await self.register_application_commands()
