from utils.database import DatabaseConnection
from datetime import datetime as dt, timedelta
import asyncpg

class Daily(object):
    all_dailys = {}

    def __init__(self, user_id:int, daily:int=0, last_daily:str=dt.utcnow(), premium:bool=False, monthly:str=dt.utcnow()):
        self.user_id = user_id
        self.daily = daily
        self.last_daily = last_daily
        self.premium = premium
        self.monthly = monthly

        self.all_dailys[self.user_id] = self

    async def save(self, db:DatabaseConnection):
        """Saves all the connected user variables"""
        try:
            await db('''
                INSERT INTO daily
                VALUES
                ($1, $2, $3, $4, $5)
                ''',
                self.user_id, self.last_daily, self.daily, self.premium, self.monthly
            )
        except asyncpg.exceptions.UniqueViolationError: 
            await db('''
                UPDATE daily SET
                last_daily=$2, daily=$3, premium=$4, monthly=$5
                WHERE
                user_id=$1
                ''',
                self.user_id, self.last_daily, self.daily, self.premium, self.monthly
            )

    @classmethod
    def get(cls, user_id:int):
        """Gets daily table's connected variables"""
        user = cls.all_dailys.get(user_id)
        if user is None:
            return cls(
                user_id = user_id,
                daily = 0,
                last_daily = dt.utcnow() - timedelta(days=3),
                premium = False,
                monthly = dt.utcnow() - timedelta(days=31),
            )
        return user


    @classmethod
    def sorted_daily(cls):
        """sorts the user's by balance. getting ranks!"""
        sorted_daily = sorted(cls.all_dailys.values(), key=lambda u: u.daily, reverse=True)
        return sorted_daily

