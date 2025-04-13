
from datetime import timedelta
from app.utils import security
from app.utils.config import settings
from app.utils.database import SessionDep
from app.apis.users.models import User
from sqlmodel import select
from app.utils.security import get_user_permissions,verify_password,create_access_token



# Example usage in endpoint dependencies

def get_user(session: SessionDep, user_id: str) -> User:
    """Fetch a User by ID from the database."""
    return session.get(User, user_id)

def get_user_by_mail(session: SessionDep, email: str) -> User:
    """Fetch a User by ID from the database."""
    return session.exec(select(User).where(User.email == email)).first()


