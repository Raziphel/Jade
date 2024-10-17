from utils.database import DatabaseConnection
from datetime import datetime as dt, timedelta
import asyncpg

class Items(object):
    all_items = {}

    def __init__(self, user_id:int, daily_saver:int=0):
        self.user_id = user_id
        self.daily_saver = daily_saver

        self.all_items[self.user_id] = self

    async def save(self, db:DatabaseConnection):
        """Saves all the connected user variables"""
        try:
            await db('''
                INSERT INTO items
                VALUES
                ($1, $2)
                ''',
                self.user_id, self.daily_saver,
            )
        except asyncpg.exceptions.UniqueViolationError: 
            await db('''
                UPDATE items SET
                thievery=$2
                WHERE
                user_id=$1
                ''',
                self.user_id, self.daily_saver
            )

    @classmethod
    def get(cls, user_id:int):
        """Gets table's connected variables"""
        user = cls.all_items.get(user_id)
        if user is None:
            return cls(
                user_id = user_id,
                daily_saver = 0,
            )
        return user