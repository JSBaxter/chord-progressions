import redis


class RedisFilterRepository(object):
    def __init__(self, host="localhost", port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)

    def write_item(self, key, item):
        """
        Writes an item to Redis. The item is stored as a hash.
        :param key: The key under which to store the item.
        :param item: The item (usually a dict) to store.
        """
        self.redis.sadd(key, item)

    def __contains__(self, key):
        """
        Checks if a key exists in Redis.
        :param key: The key to check.
        :return: True if the key exists, False otherwise.
        """
        return self.redis.exists(key)
