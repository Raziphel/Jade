from utils.database import DatabaseConnection
import asyncpg

class Coins_Record(object):
    all_coins_record = {}

    def __init__(self, user_id:int, earned:int=0, spent:int=0, taxed:int=0, lost:int=0, stolen:int=0, gifted:int=0,
                 given:int=0, won:int=0):
        self.user_id = user_id
        self.earned = earned
        self.spent = spent
        self.taxed = taxed
        self.lost = lost
        self.stolen = stolen
        self.gifted = gifted
        self.given = given
        self.won = won

        self.all_coins_record[self.user_id] = self

    async def save(self, db:DatabaseConnection):
        """Saves all the connected user variables"""
        try:
            await db('''
                INSERT INTO coins_record
                VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ''',
                self.user_id, self.earned, self.spent, self.taxed, self.lost, self.stolen, self.gifted, self.given,
                     self.won
            )
        except asyncpg.exceptions.UniqueViolationError: 
            await db('''
                UPDATE coins_record SET
                earned=$2, spent=$3, taxed=$4, lost=$5, stolen=$6, gifted=$7, given=$8, won=$9
                WHERE
                user_id=$1
                ''',
                self.user_id, self.earned, self.spent, self.taxed, self.lost, self.stolen, self.gifted, self.given,
                     self.won
            )


    @classmethod
    def get(cls, user_id:int):
        """Gets level table's connected variables"""
        user = cls.all_coins_record.get(user_id)
        if user is None:
            return cls(user_id)
        return user


    @classmethod
    def get_total_earned(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_coins_record.values():
            total += i.earned
        return total

    @classmethod
    def get_total_spent(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_coins_record.values():
            total += i.spent
        return total

    @classmethod
    def get_total_taxed(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_coins_record.values():
            total += i.taxed
        return total

    @classmethod
    def get_total_won(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_coins_record.values():
            total += i.won
        return total

    @classmethod
    def get_total_lost(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_coins_record.values():
            total += i.lost
        return total

    @classmethod
    def get_total_stolen(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_coins_record.values():
            total += i.stolen
        return total

    @classmethod
    def get_total_gifted(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_coins_record.values():
            total += i.gifted
        return total