import redis
from .config import config

redis_client = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0, decode_responses=True)

def cache_result(key, value, ttl=3600):
    redis_client.setex(key, ttl, value)

def get_cached_result(key):
    return redis_client.get(key)
