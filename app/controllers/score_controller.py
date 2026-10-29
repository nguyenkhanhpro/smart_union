from datetime import date as date_cls
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user, require_admin
from app.core.flash import flash
from app.core.templating import render
from app.database import get_db
from app.models import Criterion, SchoolClass, ScoreEntry, User
from app.services import score_service

router = APIRouter(prefix="/scores")


def _form_context(db: Session, **extra) -> dict:
    classes = db.scalars(select(SchoolClass).where(SchoolClass.is_active.is_(True)).order_by(SchoolClass.grade, SchoolClass.name)).all()
    criteria = db.scalars(select(Criterion).where(Criterion.is_active.is_(True)).order_by(Criterion.id)).all()
    return {
        "classes": classes, "criteria": criteria,
        "class_options": [(c.id, c.name) for c in classes],
        "criterion_options": [(c.id, c.name) for c in criteria],
        **extra,
    }


@router.get("")
def index(request: Request, class_id: int | None = None, criterion_id: int | None = None,
          start: str = "", end: str = "", page: int = 1,
          user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    def _d(value: str):
        try:
            return date_cls.fromisoformat(value)
        except ValueError:
            return None

    entries, total = score_service.list_entries(db, class_id, criterion_id, _d(start), _d(end), page)
    pages = max((total + settings.PER_PAGE - 1) // settings.PER_PAGE, 1)
    query = {k: v for k, v in {"class_id": class_id, "criterion_id": criterion_id, "start": start, "end": end}.items() if v}
    return render(request, "scores/index.html", _form_context(
        db, entries=entries, total=total, page=page, pages=pages, qs=urlencode(query),
        filters={"class_id": class_id, "criterion_id": criterion_id, "start": start, "end": end}))


@router.get("/new")
def new_form(request: Request, class_id: int | None = None, entry_date: str | None = None,
             user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    values = {"class_id": class_id, "kind": "sub", "entry_date": entry_date or date_cls.today().isoformat()}
    return render(request, "scores/form.html", _form_context(db, item=None, errors={}, values=values))


@router.post("/new")
def create(request: Request, class_id: int = Form(0), criterion_id: int = Form(0), kind: str = Form(""),
           amount: float = Form(0), reason: str = Form(""), entry_date: str = Form(""),
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    clean, errors = score_service.validate_entry_input(db, class_id, criterion_id, kind, amount, reason, entry_date)
    if errors:
        values = {"class_id": class_id, "criterion_id": criterion_id, "kind": kind or "sub",
                  "amount": amount or "", "reason": reason, "entry_date": entry_date}
        return render(request, "scores/form.html", _form_context(db, item=None, errors=errors, values=values), 400)
    entry = score_service.create_entry(db, user, clean)
    flash(request, f"Đã ghi {entry.points:+g} điểm cho lớp {entry.school_class.name}.")
    # Quay lại form với cùng ngày để nhập liên tiếp nhiều lượt
    return RedirectResponse(f"/scores/new?entry_date={entry.entry_date.isoformat()}", status_code=303)


@router.get("/{entry_id}/edit")
def edit_form(request: Request, entry_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    entry = db.get(ScoreEntry, entry_id)
    if not entry:
        raise HTTPException(404)
    values = {"class_id": entry.class_id, "criterion_id": entry.criterion_id,
              "kind": "add" if entry.points > 0 else "sub", "amount": abs(entry.points),
              "reason": entry.reason, "entry_date": entry.entry_date.isoformat()}
    return render(request, "scores/form.html", _form_context(db, item=entry, errors={}, values=values))


@router.post("/{entry_id}/edit")
def update(request: Request, entry_id: int, class_id: int = Form(0), criterion_id: int = Form(0), kind: str = Form(""),
           amount: float = Form(0), reason: str = Form(""), entry_date: str = Form(""),
           user: User = Depends(require_admin), db: Session = Depends(get_db)):
    entry = db.get(ScoreEntry, entry_id)
    if not entry:
        raise HTTPException(404)
    clean, errors = score_service.validate_entry_input(db, class_id, criterion_id, kind, amount, reason, entry_date)
    if errors:
        values = {"class_id": class_id, "criterion_id": criterion_id, "kind": kind or "sub",
                  "amount": amount or "", "reason": reason, "entry_date": entry_date}
        return render(request, "scores/form.html", _form_context(db, item=entry, errors=errors, values=values), 400)
    score_service.update_entry(db, user, entry, clean)
    flash(request, "Đã cập nhật lượt chấm điểm. Thay đổi được ghi vào lịch sử.")
    return RedirectResponse("/scores", status_code=303)


@router.post("/{entry_id}/delete")
def delete(request: Request, entry_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    entry = db.get(ScoreEntry, entry_id)
    if not entry:
        raise HTTPException(404)
    score_service.delete_entry(db, user, entry)
    flash(request, "Đã xóa lượt chấm điểm. Bản ghi cũ vẫn được lưu trong lịch sử.")
    return RedirectResponse("/scores", status_code=303)
