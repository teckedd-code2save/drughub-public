import uuid
import json
from datetime import timedelta
from fastapi import HTTPException
from app.utils.redis_db import set_redis_key, get_redis_key, delete_redis_key

SESSION_EXPIRE_SECONDS = 60 * 60 * 24 * 7 # 24 hours

def generate_session_token(user_id: str) -> str:
    token = str(uuid.uuid4())
    key = f"session:{token}"
    value = json.dumps({"user_id": user_id})
    set_redis_key(key, value, expiration=SESSION_EXPIRE_SECONDS)
    return token

def get_user_id_from_token(token: str) -> str:
    key = f"session:{token}"
    session_data = get_redis_key(key)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    try:
        session_json = json.loads(session_data)
        return session_json["user_id"]
    except Exception:
        raise HTTPException(status_code=401, detail="Malformed session data")

def destroy_session(token: str):
    key = f"session:{token}"
    delete_redis_key(key)
