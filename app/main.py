from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import BASE_DIR, settings
from app.controllers import (auth_controller, class_controller, criterion_controller, dashboard_controller,
                             history_controller, ranking_controller, report_controller, score_controller,
                             user_controller)
from app.core.deps import Forbidden, RedirectToLogin
from app.core.templating import render
from app.database import SessionLocal, init_db
from app.services.seed import seed_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, same_site="lax", max_age=60 * 60 * 12)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

for module in (auth_controller, dashboard_controller, ranking_controller, score_controller, class_controller,
               criterion_controller, report_controller, history_controller, user_controller):
    app.include_router(module.router)


@app.exception_handler(RedirectToLogin)
async def _redirect_to_login(request: Request, _: RedirectToLogin):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Cần đăng nhập"}, status_code=401)
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(Forbidden)
async def _forbidden(request: Request, _: Forbidden):
    return render(request, "errors/error.html", {
        "code": 403, "title": "Bạn chưa có quyền thực hiện thao tác này",
        "text": "Chức năng này dành cho tài khoản quản trị."}, status_code=403)


@app.exception_handler(StarletteHTTPException)
async def _http_error(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return render(request, "errors/error.html", {
            "code": 404, "title": "Không tìm thấy trang",
            "text": "Đường dẫn có thể đã thay đổi hoặc dữ liệu đã bị xóa."}, status_code=404)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
