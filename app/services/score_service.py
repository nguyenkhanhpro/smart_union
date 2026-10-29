"""Nghiệp vụ nhập/sửa/xóa điểm kèm ghi lịch sử thay đổi."""
import json
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Criterion, SchoolClass, ScoreEntry, ScoreHistory, User


def _snapshot(entry: ScoreEntry) -> dict:
    return {
        "class": entry.school_class.name,
        "criterion": entry.criterion.name,
        "points": entry.points,
        "reason": entry.reason,
        "date": entry.entry_date.isoformat(),
    }


def _log(db: Session, entry_id: int, action: str, user: User, old: dict | None = None, new: dict | None = None):
    db.add(ScoreHistory(
        entry_id=entry_id, action=action, changed_by=user.id,
        old_data=json.dumps(old, ensure_ascii=False) if old else None,
        new_data=json.dumps(new, ensure_ascii=False) if new else None,
    ))


def validate_entry_input(db: Session, class_id: int, criterion_id: int, kind: str,
                         amount: float, reason: str, entry_date: str) -> tuple[dict, dict]:
    """Trả về (dữ liệu sạch, lỗi theo từng trường)."""
    errors: dict[str, str] = {}
    school_class = db.get(SchoolClass, class_id)
    criterion = db.get(Criterion, criterion_id)
    if not school_class or not school_class.is_active:
        errors["class_id"] = "Chọn một lớp đang hoạt động."
    if not criterion or not criterion.is_active:
        errors["criterion_id"] = "Chọn một tiêu chí đang áp dụng."
    if kind not in ("add", "sub"):
        errors["kind"] = "Chọn cộng hoặc trừ điểm."
    if amount is None or amount <= 0:
        errors["amount"] = "Số điểm phải lớn hơn 0."
    elif amount > 100:
        errors["amount"] = "Số điểm quá lớn, kiểm tra lại."
    reason = (reason or "").strip()
    if len(reason) < 3:
        errors["reason"] = "Nhập lý do (ít nhất 3 ký tự) để minh bạch."
    try:
        parsed_date = date.fromisoformat(entry_date)
        if parsed_date > date.today():
            errors["entry_date"] = "Không chấm điểm cho ngày trong tương lai."
    except ValueError:
        parsed_date = None
        errors["entry_date"] = "Ngày không hợp lệ."

    clean = {
        "class_id": class_id, "criterion_id": criterion_id,
        "points": round(amount if kind == "add" else -amount, 2) if amount else 0,
        "reason": reason, "entry_date": parsed_date,
    }
    return clean, errors


def create_entry(db: Session, user: User, data: dict) -> ScoreEntry:
    entry = ScoreEntry(**data, created_by=user.id)
    db.add(entry)
    db.flush()
    _log(db, entry.id, "create", user, new=_snapshot(entry))
    db.commit()
    return entry


def update_entry(db: Session, user: User, entry: ScoreEntry, data: dict) -> ScoreEntry:
    old = _snapshot(entry)
    for key, value in data.items():
        setattr(entry, key, value)
    db.flush()
    db.refresh(entry)
    _log(db, entry.id, "update", user, old=old, new=_snapshot(entry))
    db.commit()
    return entry


def delete_entry(db: Session, user: User, entry: ScoreEntry) -> None:
    _log(db, entry.id, "delete", user, old=_snapshot(entry))
    db.delete(entry)
    db.commit()


def list_entries(db: Session, class_id: int | None = None, criterion_id: int | None = None,
                 start: date | None = None, end: date | None = None,
                 page: int = 1, per_page: int = settings.PER_PAGE) -> tuple[list[ScoreEntry], int]:
    conditions = []
    if class_id:
        conditions.append(ScoreEntry.class_id == class_id)
    if criterion_id:
        conditions.append(ScoreEntry.criterion_id == criterion_id)
    if start:
        conditions.append(ScoreEntry.entry_date >= start)
    if end:
        conditions.append(ScoreEntry.entry_date <= end)

    total = db.scalar(select(func.count(ScoreEntry.id)).where(*conditions)) or 0
    entries = db.scalars(
        select(ScoreEntry).where(*conditions)
        .order_by(ScoreEntry.entry_date.desc(), ScoreEntry.id.desc())
        .limit(per_page).offset((max(page, 1) - 1) * per_page)
    ).unique().all()
    return list(entries), total


def list_history(db: Session, page: int = 1, per_page: int = settings.PER_PAGE) -> tuple[list[ScoreHistory], int]:
    total = db.scalar(select(func.count(ScoreHistory.id))) or 0
    rows = db.scalars(
        select(ScoreHistory).order_by(ScoreHistory.id.desc())
        .limit(per_page).offset((max(page, 1) - 1) * per_page)
    ).unique().all()
    return list(rows), total
