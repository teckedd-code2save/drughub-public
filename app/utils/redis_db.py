from datetime import datetime
from typing import Optional
from app.utils.config import settings
from redis import Redis
from app.utils.logging_util import logger


def redis_client() -> Redis:
    if settings.ENVIRONMENT == "production":
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)
    

def set_string(key: str, value: str, expiration: int = 3600) -> bool:
    """
    Set a key-value pair in Redis
    Args:
        key (str): The key to set.
        value (str): The value to set.
        expiration (int, optional): Expiration time in seconds. Defaults to 3600.
    """
    res = redis_client().set(key, value, ex=expiration)
    if res:
        print(f"string Key '{key}' set with string value '{value}' and expiration {expiration} seconds.")
    else:
        print(f"Failed to set key '{key}'.")
    return res

def get_string(key: str) -> str:
    """
    Get a value from Redis by key
    Args:
        key (str): The key to retrieve.
    Returns:
        str: The value associated with the key, or None if not found.
    """
    value = redis_client().get(key)
    if value:
        print(f"string Key '{key}' has string value '{value}'.")
    else:
        print(f"string Key '{key}' not found.")
    return value

def set_hash(key: str, field: str, value: str, ex: Optional[int] = None) -> bool:

    """
    Set a field in a hash in Redis with an optional TTL.

    Args:
        key: The hash key.
        field: The field to set.
        value: The value to set.
        ex: Optional TTL in seconds for the key.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    client = None
    try:
        client = redis_client()
        # Set the hash field
        client.hset(key, field, value)
        logger.info(f"Hash key '{key}' with hash field '{field}' set with hash value '{value}'")
        
        # Set expiration if ex is provided
        if ex is not None:
            client.expire(key, ex)
            logger.info(f"Set TTL of {ex} seconds for key '{key}'")
        
        return True
    except Exception as e:
        logger.error(f"Error setting hash '{key}' for hash field '{field}': {str(e)}")
        return False
    finally:
        if client:
             client.close()

async def get_hash(key: str, field: str) -> str:
    """
    Get a field from a hash in Redis
    Args:
        key (str): The hash key.
        field (str): The field to retrieve.
    Returns:
        str: The value associated with the field, or None if not found.
    """
    value = redis_client().hget(key, field)
    if value:
        print(f"Hash key'{key}' for hash field '{field}' has hash value '{value}'.")
    else:
        print(f"Hash key'{key}' with hash field '{field}' not found.")
    return value

async def get_hash_all(key: str) -> dict:
    """
    Get all fields and values from a hash in Redis
    Args:
        key (str): The hash key.
    Returns:
        dict: A dictionary of all fields and values in the hash.
    """
    value = redis_client().hgetall(key)
    if value:
        print(f"Hash '{key}' has fields and values: {value}.")
    else:
        print(f"Hash '{key}' not found.")
    return value

async def key_delete(key:str):
    res = redis_client().delete(key)
    

