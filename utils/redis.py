import redis
import toml


class RedisUtils:
    def __init__(self, config_path='secret.toml'):
        # Load the configuration from the secret.toml file
        config = toml.load(config_path)['redis']

        # Initialize the Redis connection using the loaded config
        self.redis = redis.Redis(
            host=config.get('host', 'localhost'),
            port=config.get('port', 6379),
            db=config.get('db', 0),
            password=config.get('password', None)
        )

    def is_connected(self):
        try:
            return self.redis.ping()
        except redis.ConnectionError:
            return False

    def get_value(self, key):
        try:
            return self.redis.get(key)
        except redis.RedisError as e:
            return f"Redis error: {e}"

    def set_value(self, key, value):
        try:
            self.redis.set(key, value)
            return True
        except redis.RedisError as e:
            return f"Redis error: {e}"
