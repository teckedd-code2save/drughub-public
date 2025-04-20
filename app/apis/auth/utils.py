import datetime
import json


def get_session_key(user_id:str):
    return f"sessions:{user_id}"



# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)