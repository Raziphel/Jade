import toml
import logging
import openai

from discord.ext import commands
from discord import AllowedMentions

import utils
from utils.database import DatabaseConnection
from utils.redis import RedisUtils  # Import RedisUtils


# + ------------------------- Serpent Main Class
class Serpent(commands.AutoShardedBot):
    def __init__(self, config: str, secret: str, *args, logger: logging.Logger = None, **kwargs):
        super().__init__(*args, fetch_offline_members=True, guild_subscriptions=True,
                         allowed_mentions=AllowedMentions(roles=True, users=True, everyone=True), **kwargs)

        self.logger = logger or logging.getLogger("Serpent")
        self.config_path = config
        self.secret_path = secret

        # Load config and secret
        with open(self.config_path) as z:
            self.config = toml.load(z)

        with open(self.secret_path) as z:
            self.secret = toml.load(z)

        # + Load Utils
        utils.Embed.bot = self
        utils.CoinFunctions.bot = self
        utils.UserFunctions.bot = self

        # + Initialize Redis
        self.redis = RedisUtils(config_path=self.secret_path)

        # + Initialize the MessageEditManager
        self.message_edit_manager = utils.API_Manager()

        # + Get OpenAI key setup
        openai.api_key = self.secret['openai_key']

        # + Initialize Database
        self.database = DatabaseConnection
        self.database.config = self.secret['database']

        # Startup state flags
        self.startup_method = None
        self.connected = False

    def run(self):
        self.startup_method = self.loop.create_task(self.startup())
        super().run(self.secret['token'])

    async def startup(self):
        """Load the database and set up Redis"""
        try:
            # Step 1: Load database
            await self.initialize_database()

            # Step 2: Initialize Redis listener (if needed)
            await self.start_redis_listeners()

            # + Start the MessageEditManager queue processor
            self.message_edit_manager.start_processing(self.loop)

            # + Register slash commands
            await self.register_application_commands()

        except Exception as e:
            print(f"Startup failed: {e}")

    async def initialize_database(self):
        """Load and cache data from the database"""
        try:
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
                'lottery': utils.Lottery
            }

            # Clear all caches dynamically
            for utility_class in table_mapping.values():
                if hasattr(utility_class, 'clear_all'):
                    utility_class.clear_all()  # Assuming each class has a 'clear_all' method to clear the cache
                else:
                    cache_attr = [attr for attr in dir(utility_class) if attr.startswith('all_')]
                    if cache_attr:
                        getattr(utility_class, cache_attr[0]).clear()  # Clear the first 'all_*' attribute found

            # Collect data from the database dynamically
            async with self.database() as db:
                data_collections = {}
                for table in table_mapping.keys():
                    data_collections[table] = await db(f'SELECT * FROM {table}')  # Fetch data for each table

            # Cache all data into local objects dynamically
            for table, rows in data_collections.items():
                utility_class = table_mapping[table]
                for row in rows:
                    utility_class(**row)  # Instantiate and cache the utility objects dynamically

            # Validate if the database is connected correctly
            lvl = utils.Levels.get(159516156728836097)
            if lvl.level == 0:
                raise Exception("Database connection validation failed. Level data is incorrect.")
            else:
                print('Bot database is connected!')

        except Exception as e:
            print(f"Couldn't connect to the database... :: {e}")
            raise

    async def start_redis_listeners(self):
        """Start Redis pub/sub listener for background processing (optional)"""
        if self.redis.is_connected():
            print("Connected to Redis!")
            pubsub = self.redis.subscribe('server-events')

            async def listen_for_redis_messages():
                for message in pubsub.listen():
                    if message['type'] == 'message':
                        await self.process_redis_message(message['data'])

            # Run Redis listener as a background task
            self.loop.create_task(listen_for_redis_messages())
        else:
            print("Failed to connect to Redis.")

    async def process_redis_message(self, message):
        """Process Redis messages for internal use"""
        # Handle messages from Redis (e.g., syncing game states, etc.)
        # Example: Process events based on your server's messages
        print(f"Received Redis message: {message}")
