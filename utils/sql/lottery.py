from utils.database import DatabaseConnection
from datetime import datetime as dt, timedelta
import asyncpg

class Lottery(object):
    all_lotterys = {}

    def __init__(self, lottery_id:int, last_winner_id:int, last_amount:int, coins:int, lot_time:str, last_msg_id:int):
        self.lottery_id = lottery_id
        self.last_winner_id = last_winner_id
        self.last_amount = last_amount
        self.coins = coins
        self.lot_time = lot_time
        self.last_msg_id = last_msg_id
        self.all_lotterys[self.lottery_id] = self

    async def save(self, db:DatabaseConnection):
        """Saves all the connected user variables"""
        try:
            await db('''
                INSERT INTO lottery
                VALUES
                ($1, $2, $3, $4, $5, $6)
                ''',
            self.lottery_id, self.last_winner_id, self.last_amount, self.coins, self.lot_time, self.last_msg_id
            )
        except asyncpg.exceptions.UniqueViolationError:
            await db('''
                UPDATE lottery SET
                last_winner_id=$2, last_amount=$3, coins=$4, lot_time=$5, last_msg_id=$6
                WHERE
                lottery_id=$1
                ''',
                self.lottery_id, self.last_winner_id, self.last_amount, self.coins, self.lot_time, self.last_msg_id
            )

    @classmethod
    def get(cls, lot_id:int):
        """Gets level table's connected variables"""
        lot = cls.all_lotterys.get(lot_id)
        if lot is None:
            return cls(
                lottery_id = lot_id,
                last_winner_id = 0,
                last_amount = 0,
                coins = 0,
                last_msg_id = 0,
                lot_time = dt.utcnow(),
            )
        return lot

