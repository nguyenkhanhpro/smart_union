"""Dependency dùng chung cho Controller: xác thực và phân quyền."""
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


class RedirectToLogin(Exception):
    pass


class Forbidden(Exception):
    pass


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        request.session.clear()
        raise RedirectToLogin()
    request.state.user = user
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise Forbidden()
    return user
