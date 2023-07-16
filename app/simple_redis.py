import os
import json
import redis

redis_client = redis.StrictRedis(
    host="inkwell-basic-cache.redis.cache.windows.net",
    port=6380,
    db=0,
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,
)
redis_client.ping()


def redis_store(key, value):
    redis_client.set(key, json.dumps(value))


def redis_retrieve(key):
    return json.loads(redis_client.get(key))


def redis_check(key):
    return redis_client.exists(key)
