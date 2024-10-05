from utils.database import DatabaseConnection
import asyncpg

class Currency(object):
    all_currency = {}

    def __init__(self, user_id:int, coins:int=0, tickets:int=0):
        self.user_id = user_id
        self.coins = coins
        self.tickets = tickets

        self.all_currency[self.user_id] = self

    async def save(self, db:DatabaseConnection):
        """Saves all the connected user variables"""
        try:
            await db('''
                INSERT INTO currency
                VALUES
                ($1, $2, $3)
                ''',
                self.user_id, self.coins, self.tickets
            )
        except asyncpg.exceptions.UniqueViolationError: 
            await db('''
                UPDATE currency SET
                coins=$2, tickets=$3
                WHERE
                user_id=$1
                ''',
                self.user_id, self.coins, self.tickets
            )

    @classmethod
    def get(cls, user_id:int):
        """Gets level table's connected variables"""
        user = cls.all_currency.get(user_id)
        if user is None:
            return cls(user_id)
        return user

    @classmethod
    def sort_coins(cls):
        """sorts the user's by balance. getting ranks!"""
        sorted_coins = sorted(cls.all_currency.values(), key=lambda u: u.coins, reverse=True)
        return sorted_coins


    @classmethod 
    def get_total_coins(cls):
        """Gets all the user's collected amount of gold"""
        total = 0
        for i in cls.all_currency.values():
            total += i.coins
        return total


    @classmethod
    def delete(cls, user_id:int):
        """Removes a user from cache via their ID, fails silently if not present"""
        try:
            del cls.all_currency[user_id]
        except KeyError:
            pass


    @classmethod
    def sort_tickets(cls):
        """sorts the user's by tickets. getting ranks!"""
        sorted_tickets = sorted(cls.all_currency.values(), key=lambda u: u.tickets, reverse=True)
        return sorted_tickets

    @classmethod
    def get_total_tickets(cls):
        """Gets total tickets"""
        total = 0
        for i in cls.all_currency.values():
            total += i.tickets
        return total

    @classmethod
    async def get_all_users_from_db(cls, db: DatabaseConnection):
        """Fetch all users from the database, including those not in the cache"""
        users = await db('SELECT user_id, coins, tickets FROM currency')
        all_users = []

        for user_data in users:
            user_id, coins, tickets = user_data
            if user_id not in cls.all_currency:
                # Create a Currency object if not in the cache
                cls(user_id, coins, tickets)
            else:
                # Update the cached user with the database values
                user = cls.all_currency[user_id]
                user.coins = coins
                user.tickets = tickets

            all_users.append(cls.all_currency[user_id])  # Append user from cache

        return all_users