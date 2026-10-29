from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.core.flash import flash
from app.core.templating import render
from app.database import get_db
from app.models import SchoolClass, ScoreEntry, User
from app.services.period import period_from_params
from app.services.ranking_service import criterion_breakdown, get_ranking
from app.services.score_service import list_entries

router = APIRouter(prefix="/classes")


def _validate(db: Session, name: str, grade: int, school_year: str, current_id: int | None = None) -> dict:
    errors = {}
    if not name.strip():
        errors["name"] = "Nhập tên lớp."
    else:
        existing = db.scalar(select(SchoolClass).where(SchoolClass.name == name.strip()))
        if existing and existing.id != current_id:
            errors["name"] = "Tên lớp này đã tồn tại."
    if not 1 <= grade <= 12:
        errors["grade"] = "Khối từ 1 đến 12."
    if not school_year.strip():
        errors["school_year"] = "Nhập năm học, ví dụ 2026-2027."
    return errors


@router.get("")
def index(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(SchoolClass, func.count(ScoreEntry.id)).outerjoin(ScoreEntry)
        .group_by(SchoolClass.id).order_by(SchoolClass.grade, SchoolClass.name)
    ).unique().all()
    return render(request, "classes/index.html", {"rows": rows})


@router.get("/new")
def new_form(request: Request, user: User = Depends(require_admin)):
    return render(request, "classes/form.html", {"item": None, "errors": {}, "values": {"is_active": True}})


@router.post("/new")
def create(request: Request, name: str = Form(""), grade: int = Form(0), school_year: str = Form(""),
           homeroom_teacher: str = Form(""), note: str = Form(""),
           user: User = Depends(require_admin), db: Session = Depends(get_db)):
    errors = _validate(db, name, grade, school_year)
    if errors:
        values = dict(name=name, grade=grade or "", school_year=school_year, homeroom_teacher=homeroom_teacher, note=note, is_active=True)
        return render(request, "classes/form.html", {"item": None, "errors": errors, "values": values}, 400)
    db.add(SchoolClass(name=name.strip(), grade=grade, school_year=school_year.strip(),
                       homeroom_teacher=homeroom_teacher.strip(), note=note.strip()))
    db.commit()
    flash(request, f"Đã thêm lớp {name.strip()}.")
    return RedirectResponse("/classes", status_code=303)


@router.get("/{class_id}")
def detail(request: Request, class_id: int, kind: str = "week", date: str | None = None,
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(SchoolClass, class_id)
    if not item:
        raise HTTPException(404)
    period = period_from_params(kind, date)
    ranking = get_ranking(db, period, with_change=True)
    entries, _ = list_entries(db, class_id=class_id, start=period.start, end=period.end, per_page=100)
    return render(request, "classes/detail.html", {
        "item": item, "period": period,
        "row": next((r for r in ranking if r.class_id == class_id), None),
        "class_total": len(ranking),
        "breakdown": criterion_breakdown(db, period, class_id),
        "entries": entries,
    })


@router.get("/{class_id}/edit")
def edit_form(request: Request, class_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(SchoolClass, class_id)
    if not item:
        raise HTTPException(404)
    return render(request, "classes/form.html", {"item": item, "errors": {}, "values": vars(item)})


@router.post("/{class_id}/edit")
def update(request: Request, class_id: int, name: str = Form(""), grade: int = Form(0), school_year: str = Form(""),
           homeroom_teacher: str = Form(""), note: str = Form(""), is_active: str | None = Form(None),
           user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(SchoolClass, class_id)
    if not item:
        raise HTTPException(404)
    errors = _validate(db, name, grade, school_year, current_id=class_id)
    if errors:
        values = dict(name=name, grade=grade or "", school_year=school_year, homeroom_teacher=homeroom_teacher,
                      note=note, is_active=bool(is_active))
        return render(request, "classes/form.html", {"item": item, "errors": errors, "values": values}, 400)
    item.name, item.grade, item.school_year = name.strip(), grade, school_year.strip()
    item.homeroom_teacher, item.note, item.is_active = homeroom_teacher.strip(), note.strip(), bool(is_active)
    db.commit()
    flash(request, f"Đã cập nhật lớp {item.name}.")
    return RedirectResponse("/classes", status_code=303)


@router.post("/{class_id}/delete")
def delete(request: Request, class_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(SchoolClass, class_id)
    if not item:
        raise HTTPException(404)
    if db.scalar(select(func.count(ScoreEntry.id)).where(ScoreEntry.class_id == class_id)):
        flash(request, f"Lớp {item.name} đã có điểm nên không thể xóa. Hãy bỏ chọn “Đang hoạt động” để ẩn lớp khỏi bảng xếp hạng.", "warning")
    else:
        db.delete(item)
        db.commit()
        flash(request, f"Đã xóa lớp {item.name}.")
    return RedirectResponse("/classes", status_code=303)
