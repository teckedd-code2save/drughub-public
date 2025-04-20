from datetime import datetime
from app.utils.config import settings
from redis import Redis

def redis_client() -> Redis:
    if settings.ENVIRONMENT == "staging":
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)
    

async def set_redis_key(key: str, value: str, expiration: int = 3600) -> None:
    """
    Set a key-value pair in Redis
    Args:
        key (str): The key to set.
        value (str): The value to set.
        expiration (int, optional): Expiration time in seconds. Defaults to 3600.
    """
    res = redis_client().set(key, value, ex=expiration)
    if res:
        print(f"Key '{key}' set with value '{value}' and expiration {expiration} seconds.")
    else:
        print(f"Failed to set key '{key}'.")

async def get_redis_key(key: str) -> str:
    """
    Get a value from Redis by key
    Args:
        key (str): The key to retrieve.
    Returns:
        str: The value associated with the key, or None if not found.
    """
    value = redis_client().get(key)
    if value:
        print(f"Key '{key}' has value '{value}'.")
    else:
        print(f"Key '{key}' not found.")
    return value

async def delete_redis_key(key:str):
    res = redis_client().delete(key)
    

