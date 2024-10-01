from utils.database import DatabaseConnection
import asyncpg

class UserLink(object):
    all_user_links = {}

    def __init__(self, discord_id: int, steam_id: str):
        self.discord_id = discord_id
        self.steam_id = steam_id

        # Store the user link in the class-level dictionary
        self.all_user_links[(self.discord_id, self.steam_id)] = self

    async def save(self, db: DatabaseConnection):
        """Saves or updates the user link in the database."""
        try:
            await db('''
                INSERT INTO user_link (discord_id, steam_id)
                VALUES
                ($1, $2)
                ''',
                self.discord_id, self.steam_id
            )
        except asyncpg.exceptions.UniqueViolationError:
            # If the combination already exists, you can choose to handle it here if needed
            pass

    @classmethod
    def get(cls, discord_id: int, steam_id: str):
        """Gets a user link object based on discord_id and steam_id."""
        user_link = cls.all_user_links.get((discord_id, steam_id))
        if user_link is None:
            return cls(discord_id, steam_id)
        return user_link

    @classmethod
    def delete(cls, discord_id: int, steam_id: str):
        """Removes a user link from cache via their IDs, fails silently if not present."""
        try:
            del cls.all_user_links[(discord_id, steam_id)]
        except KeyError:
            pass
