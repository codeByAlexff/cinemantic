#Redis Cache File For Organization
import redis
from redis.exceptions import RedisError
import json
import hashlib
from config import TTL

red = redis.Redis(
    host="localhost",
    port=6379,
    socket_connect_timeout=5,
    socket_timeout=2,
    decode_responses=True
    )

#Normalize-Hash-Prefix
def make_key(model, text):
    clean = text.lower().strip()
    digest = hashlib.sha256(clean.encode("utf-8")).hexdigest()
    return f"emb:{model}:{digest}"

def get_vector(key):
    #Returns cached vector or Error on miss
    try:
        raw = red.get(key)
    except (RedisError, OSError) as e:
            print(f"cached read failed: {e}")
            return None
    return json.loads(raw) if raw else None

def set_vector(key, vec, ttl=TTL):
    try:
         red.set(key, json.dumps(vec), ex=ttl)
    except (RedisError, OSError) as e:
        print(f"cache write failed: {e}")
          
def ping():
    try:
        return red.ping()
    except (RedisError, OSError):
        return False
