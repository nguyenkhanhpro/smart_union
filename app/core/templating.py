"""Cấu hình Jinja2 (tầng View) và hàm render dùng chung cho mọi Controller."""
from datetime import date, datetime

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR, settings
from app.core.flash import pop_flash

templates = Jinja2Templates(directory=str(BASE_DIR / "views"))


def _num(value) -> str:
    if value is None:
        return "0"
    value = float(value)
    return str(int(value)) if value == int(value) else f"{value:.1f}"


def _points(value) -> str:
    """+5 / −3 / 0 — dùng dấu trừ typographic để dễ nhìn."""
    if not value:
        return "0"
    value = float(value)
    return f"+{_num(value)}" if value > 0 else f"−{_num(abs(value))}"


def _date_vn(value) -> str:
    return value.strftime("%d/%m/%Y") if isinstance(value, (date, datetime)) else ""


def _datetime_vn(value) -> str:
    return value.strftime("%H:%M %d/%m/%Y") if isinstance(value, datetime) else ""


templates.env.filters.update(num=_num, points=_points, date_vn=_date_vn, datetime_vn=_datetime_vn)
templates.env.globals["app_name"] = settings.APP_NAME


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    ctx = {
        "user": getattr(request.state, "user", None),
        "flash": pop_flash(request),
        "current_path": request.url.path,
        "today": date.today(),
    }
    ctx.update(context or {})
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
