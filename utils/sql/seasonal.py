from utils.database import DatabaseConnection
import asyncpg

class Seasonal(object):
    all_seasonal = {}

    def __init__(self, user_id:int, presents_given:int=0, presents_coins_given:int=0):
        self.user_id = user_id
        self.presents_given = presents_given
        self.presents_coins_given = presents_coins_given

        self.all_seasonal[self.user_id] = self

    async def save(self, db:DatabaseConnection):
        """Saves all the connected user variables"""
        try:
            await db('''
                INSERT INTO seasonal
                VALUES
                ($1, $2, $3)
                ''',
                self.user_id, self.presents_given, self.presents_coins_given
            )
        except asyncpg.exceptions.UniqueViolationError: 
            await db('''
                UPDATE seasonal SET
                presents_given=$2, presents_coins_given=$3
                WHERE
                user_id=$1
                ''',
                self.user_id, self.presents_given, self.presents_coins_given
            )

    @classmethod
    def get(cls, user_id:int):
        """Gets level table's connected variables"""
        user = cls.all_seasonal.get(user_id)
        if user is None:
            return cls(user_id)
        return user

    @classmethod
    def sort_presents_given(cls):
        """sorts the user's by balance. getting ranks!"""
        sorted_presents_given = sorted(cls.all_seasonal.values(), key=lambda u: u.presents_given, reverse=True)
        return sorted_presents_given


    @classmethod 
    def get_total_presents_given(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_seasonal.values():
            total += i.presents_given
        return total

    @classmethod
    def sort_presents_coins_given(cls):
        """sorts the user's by presents_coins_given. getting ranks!"""
        sorted_presents_coins_given = sorted(cls.all_seasonal.values(), key=lambda u: u.presents_coins_given, reverse=True)
        return sorted_presents_coins_given

    @classmethod
    def get_total_presents_coins_given(cls):
        """Gets total presents_coins_given"""
        total = 0
        for i in cls.all_seasonal.values():
            total += i.presents_coins_given
        return total
