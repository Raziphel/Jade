from utils.database import DatabaseConnection
from datetime import datetime as dt, timedelta
import asyncpg

class Skills(object):
    all_skills = {}

    def __init__(self, user_id:int, thievery:bool=False, larceny:bool=False, larceny_stamp:str=dt.utcnow(), connect4:bool=False, blackjack:bool=False):
        self.user_id = user_id
        self.thievery = thievery
        self.larceny = larceny
        self.larceny_stamp = larceny_stamp
        self.connect4 = connect4
        self.blackjack = blackjack

        self.all_skills[self.user_id] = self

    async def save(self, db:DatabaseConnection):
        """Saves all the connected user variables"""
        try:
            await db('''
                INSERT INTO skills
                VALUES
                ($1, $2, $3, $4, $5, $6)
                ''',
                self.user_id, self.thievery, self.larceny, self.larceny_stamp, self.connect4, self.blackjack
            )
        except asyncpg.exceptions.UniqueViolationError: 
            await db('''
                UPDATE skills SET
                thievery=$2, larceny=$3, larceny_stamp=$4, connect4=$5, blackjack=$6
                WHERE
                user_id=$1
                ''',
                self.user_id, self.thievery, self.larceny, self.larceny_stamp, self.connect4, self.blackjack
            )

    @classmethod
    def get(cls, user_id:int):
        """Gets table's connected variables"""
        user = cls.all_skills.get(user_id)
        if user is None:
            return cls(
                user_id = user_id,
                thievery = False,
                larceny = False,
                larceny_stamp = dt.utcnow() - timedelta(days=1),
                connect4 = False,
                blackjack = False,
            )
        return user