from utils.database import DatabaseConnection
from datetime import datetime as dt, timedelta
import asyncpg

class Tracking(object):
    all_tracking = {}

    def __init__(self, user_id:int, messages:int=0, vc_mins:int=0, last_bump:str=dt.now(), color:int=0xff69b4):
        self.user_id = user_id
        self.messages = messages
        self.vc_mins = vc_mins
        self.last_bump = last_bump
        self.color = color

        self.all_tracking[self.user_id] = self

    async def save(self, db:DatabaseConnection):
        """Saves all the connected user variables"""
        try:
            await db('''
                INSERT INTO tracking
                VALUES
                ($1, $2, $3, $4, $5)
                ''',
                self.user_id, self.messages, self.vc_mins, self.last_bump, self.color
            )
        except asyncpg.exceptions.UniqueViolationError: 
            await db('''
                UPDATE tracking SET
                messages=$2, vc_mins=$3, last_bump=$4, color=$5
                WHERE
                user_id=$1
                ''',
                self.user_id, self.messages, self.vc_mins, self.last_bump, self.color
            )

    @classmethod
    def get(cls, user_id:int):
        """Gets level table's connected variables"""
        user = cls.all_tracking.get(user_id)
        if user is None:
            return cls(user_id)
        return user


    @classmethod
    def sorted_messages(cls):
        """sorts the user's by balance. getting ranks!"""
        sorted_messages = sorted(cls.all_tracking.values(), key=lambda u: u.messages, reverse=True)
        return sorted_messages



    @classmethod
    def sorted_vc_mins(cls):
        """sorts the user's by balance. getting ranks!"""
        sorted_vc_mins = sorted(cls.all_tracking.values(), key=lambda u: u.vc_mins, reverse=True)
        return sorted_vc_mins