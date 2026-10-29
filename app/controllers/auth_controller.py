from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.templating import render
from app.database import get_db
from app.services.auth_service import authenticate

router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return render(request, "auth/login.html")


@router.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form(""), db: Session = Depends(get_db)):
    user = authenticate(db, username, password)
    if not user:
        return render(request, "auth/login.html",
                      {"error": "Tên đăng nhập hoặc mật khẩu chưa đúng.", "username": username}, status_code=400)
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
