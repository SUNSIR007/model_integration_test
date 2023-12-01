import redis


class RedisCache:

    def __init__(self, redis_url: str):
        self.pool = redis.ConnectionPool().from_url(redis_url, decode_responses=True)
        self.conn = redis.Redis(connection_pool=self.pool)

    def set(self, openid, value, ex=10 * 60):
        self.conn.set(openid, value, ex=ex)

    def delete(self, openid):
        self.conn.delete(openid)

    def get(self, openid):
        val = self.conn.get(openid)
        return None if val is None else int(val)
