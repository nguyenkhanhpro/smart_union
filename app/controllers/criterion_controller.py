from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.core.flash import flash
from app.core.templating import render
from app.database import get_db
from app.models import Criterion, ScoreEntry, User

router = APIRouter(prefix="/criteria")


def _validate(db: Session, name: str, current_id: int | None = None) -> dict:
    if not name.strip():
        return {"name": "Nhập tên tiêu chí."}
    existing = db.scalar(select(Criterion).where(Criterion.name == name.strip()))
    if existing and existing.id != current_id:
        return {"name": "Tên tiêu chí này đã tồn tại."}
    return {}


@router.get("")
def index(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Criterion, func.count(ScoreEntry.id)).outerjoin(ScoreEntry).group_by(Criterion.id).order_by(Criterion.id)
    ).unique().all()
    return render(request, "criteria/index.html", {"rows": rows})


@router.get("/new")
def new_form(request: Request, user: User = Depends(require_admin)):
    return render(request, "criteria/form.html", {"item": None, "errors": {}, "values": {"is_active": True}})


@router.post("/new")
def create(request: Request, name: str = Form(""), description: str = Form(""),
           user: User = Depends(require_admin), db: Session = Depends(get_db)):
    errors = _validate(db, name)
    if errors:
        return render(request, "criteria/form.html", {"item": None, "errors": errors,
                      "values": {"name": name, "description": description, "is_active": True}}, 400)
    db.add(Criterion(name=name.strip(), description=description.strip()))
    db.commit()
    flash(request, f"Đã thêm tiêu chí {name.strip()}.")
    return RedirectResponse("/criteria", status_code=303)


@router.get("/{criterion_id}/edit")
def edit_form(request: Request, criterion_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(Criterion, criterion_id)
    if not item:
        raise HTTPException(404)
    return render(request, "criteria/form.html", {"item": item, "errors": {}, "values": vars(item)})


@router.post("/{criterion_id}/edit")
def update(request: Request, criterion_id: int, name: str = Form(""), description: str = Form(""),
           is_active: str | None = Form(None),
           user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(Criterion, criterion_id)
    if not item:
        raise HTTPException(404)
    errors = _validate(db, name, current_id=criterion_id)
    if errors:
        return render(request, "criteria/form.html", {"item": item, "errors": errors,
                      "values": {"name": name, "description": description, "is_active": bool(is_active)}}, 400)
    item.name, item.description, item.is_active = name.strip(), description.strip(), bool(is_active)
    db.commit()
    flash(request, f"Đã cập nhật tiêu chí {item.name}.")
    return RedirectResponse("/criteria", status_code=303)


@router.post("/{criterion_id}/delete")
def delete(request: Request, criterion_id: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = db.get(Criterion, criterion_id)
    if not item:
        raise HTTPException(404)
    if db.scalar(select(func.count(ScoreEntry.id)).where(ScoreEntry.criterion_id == criterion_id)):
        flash(request, f"Tiêu chí {item.name} đã có điểm nên không thể xóa. Hãy bỏ chọn “Đang áp dụng” để ngừng sử dụng.", "warning")
    else:
        db.delete(item)
        db.commit()
        flash(request, f"Đã xóa tiêu chí {item.name}.")
    return RedirectResponse("/criteria", status_code=303)
