from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.core.flash import flash
from app.core.security import hash_password
from app.core.templating import render
from app.database import get_db
from app.models import ROLE_ADMIN, ROLE_TEACHER, User

router = APIRouter(prefix="/users")
ROLES = [(ROLE_TEACHER, "Giáo viên"), (ROLE_ADMIN, "Quản trị")]


def _validate(db: Session, username: str, full_name: str, role: str, password: str,
              current: User | None) -> dict:
    errors = {}
    if current is None:
        if not username.strip():
            errors["username"] = "Nhập tên đăng nhập."
        elif db.scalar(select(User).where(User.username == username.strip())):
            errors["username"] = "Tên đăng nhập đã được dùng."
        if len(password) < 6:
            errors["password"] = "Mật khẩu tối thiểu 6 ký tự."
    elif password and len(password) < 6:
        errors["password"] = "Mật khẩu mới tối thiểu 6 ký tự."
    if not full_name.strip():
        errors["full_name"] = "Nhập họ tên."
    if role not in (ROLE_ADMIN, ROLE_TEACHER):
        errors["role"] = "Chọn vai trò."
    return errors


@router.get("")
def index(request: Request, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.role, User.full_name)).all()
    return render(request, "users/index.html", {"users": users})


@router.get("/new")
def new_form(request: Request, user: User = Depends(require_admin)):
    return render(request, "users/form.html", {"item": None, "errors": {}, "roles": ROLES,
                                               "values": {"role": ROLE_TEACHER, "is_active": True}})


@router.post("/new")
def create(request: Request, username: str = Form(""), full_name: str = Form(""), role: str = Form(""),
           password: str = Form(""), user: User = Depends(require_admin), db: Session = Depends(get_db)):
    errors = _validate(db, username, full_name, role, password, None)
    if errors:
        return render(request, "users/form.html", {"item": None, "errors": errors, "roles": ROLES,
                      "values": {"username": username, "full_name": full_name, "role": role, "is_active": True}}, 400)
    db.add(User(username=username.strip(), full_name=full_name.strip(), role=role, password_hash=hash_password(password)))
    db.commit()
    flash(request, f"Đã tạo tài khoản {username.strip()}.")
    return RedirectResponse("/users", status_code=303)


@router.get("/{user_id}/edit")
def edit_form(request: Request, user_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(404)
    return render(request, "users/form.html", {"item": item, "errors": {}, "roles": ROLES, "values": vars(item)})


@router.post("/{user_id}/edit")
def update(request: Request, user_id: int, full_name: str = Form(""), role: str = Form(""), password: str = Form(""),
           is_active: str | None = Form(None), user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(404)
    errors = _validate(db, item.username, full_name, role, password, item)
    if item.id == user.id and (role != ROLE_ADMIN or not is_active):
        errors["role"] = "Bạn không thể tự hạ quyền hoặc khóa tài khoản của chính mình."
    if errors:
        return render(request, "users/form.html", {"item": item, "errors": errors, "roles": ROLES,
                      "values": {"username": item.username, "full_name": full_name, "role": role, "is_active": bool(is_active)}}, 400)
    item.full_name, item.role, item.is_active = full_name.strip(), role, bool(is_active)
    if password:
        item.password_hash = hash_password(password)
    db.commit()
    flash(request, f"Đã cập nhật tài khoản {item.username}.")
    return RedirectResponse("/users", status_code=303)
