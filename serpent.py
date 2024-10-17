import toml
import logging
import openai

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

        # + Initialize the MessageEditManager
        self.message_edit_manager = utils.API_Manager()

        # Initialize Redis with the loaded configuration
        redis_config = self.secret.get('redis')
        self.redis_utils = utils.RedisUtils(config=redis_config)  # Pass Redis config here

        #+ Get OpenAI key setup
        openai.api_key = self.secret['openai_key']

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
            # Define a mapping of table names to their corresponding utility classes
            table_mapping = {
                'moderation': utils.Moderation,
                'levels': utils.Levels,
                'currency': utils.Currency,
                'coins_record': utils.Coins_Record,
                'tracking': utils.Tracking,
                'daily': utils.Daily,
                'skills': utils.Skills,
                'user_link': utils.UserLink,
                'lottery': utils.Lottery,
                'items': utils.Items
            }

            # Step 1: Clear all caches dynamically
            for utility_class in table_mapping.values():
                if hasattr(utility_class, 'clear_all'):
                    utility_class.clear_all()  # Assuming each class has a 'clear_all' method to clear the cache
                else:
                    cache_attr = [attr for attr in dir(utility_class) if attr.startswith('all_')]
                    if cache_attr:
                        getattr(utility_class, cache_attr[0]).clear()  # Clear the first 'all_*' attribute found

            # Step 2: Collect data from the database dynamically
            async with self.database() as db:
                data_collections = {}
                for table in table_mapping.keys():
                    data_collections[table] = await db(f'SELECT * FROM {table}')  # Fetch data for each table

            # Step 3: Cache all data into local objects dynamically
            for table, rows in data_collections.items():
                utility_class = table_mapping[table]
                for row in rows:
                    utility_class(**row)  # Instantiate and cache the utility objects dynamically


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

        # Check Redis connection
        if not self.redis_utils.is_connected():
            print("Failed to connect to Redis!")
            self.connected = False
        print("Connected to Redis!")

        # + Start the MessageEditManager queue processor
        self.message_edit_manager.start_processing(self.loop)

        #+ Register slash commands
        await self.register_application_commands()
