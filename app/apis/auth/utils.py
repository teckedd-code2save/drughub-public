import datetime
import json


def user_sessions_key(user_id:str):
    return f"sessions:{user_id}"


def login_session_key(session_id:str):
    return f"sessions:account:{session_id}"


# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)