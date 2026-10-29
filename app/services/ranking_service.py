"""Tính điểm và xếp hạng. Mọi phép tính điểm nằm ở đây (SQL + Python thuần, kiểm chứng được)."""
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Criterion, SchoolClass, ScoreEntry
from app.services.period import Period, resolve_period


@dataclass
class RankRow:
    class_id: int
    class_name: str
    homeroom_teacher: str
    positive: float
    negative: float
    entries_count: int
    total: float
    rank: int = 0
    change: int | None = None   # >0: tăng hạng, <0: giảm hạng, None: không có kỳ trước để so sánh


@dataclass
class CriterionRow:
    criterion_id: int
    name: str
    positive: float
    negative: float
    count: int

    @property
    def net(self) -> float:
        return round(self.positive + self.negative, 2)


def _aggregate(db: Session, period: Period) -> list[RankRow]:
    pos = func.coalesce(func.sum(case((ScoreEntry.points > 0, ScoreEntry.points), else_=0)), 0)
    neg = func.coalesce(func.sum(case((ScoreEntry.points < 0, ScoreEntry.points), else_=0)), 0)
    stmt = (
        select(SchoolClass.id, SchoolClass.name, SchoolClass.homeroom_teacher, pos, neg, func.count(ScoreEntry.id))
        .select_from(SchoolClass)
        .outerjoin(ScoreEntry, and_(ScoreEntry.class_id == SchoolClass.id,
                                    ScoreEntry.entry_date.between(period.start, period.end)))
        .where(SchoolClass.is_active.is_(True))
        .group_by(SchoolClass.id)
    )
    return [
        RankRow(cid, name, teacher or "", round(p, 2), round(n, 2), cnt, round(settings.BASE_SCORE + p + n, 2))
        for cid, name, teacher, p, n, cnt in db.execute(stmt).all()
    ]


def _assign_ranks(rows: list[RankRow]) -> list[RankRow]:
    """Xếp hạng kiểu 1-2-2-4.

    Quy tắc đồng điểm (chỉnh theo quy chế trường tại hàm `_sort_key`):
      1) tổng điểm cao hơn xếp trên;
      2) nếu bằng nhau, lớp bị trừ ít điểm hơn xếp trên;
      3) vẫn bằng nhau thì đồng hạng.
    """
    def _sort_key(r: RankRow):
        return (-r.total, -r.negative)

    rows = sorted(rows, key=lambda r: (_sort_key(r), r.class_name))
    prev_key, prev_rank = None, 0
    for index, row in enumerate(rows, start=1):
        key = _sort_key(row)
        row.rank = prev_rank if key == prev_key else index
        prev_key, prev_rank = key, row.rank
    return rows


def get_ranking(db: Session, period: Period, with_change: bool = False) -> list[RankRow]:
    ranked = _assign_ranks(_aggregate(db, period))
    if with_change:
        prev_rows = _aggregate(db, resolve_period(period.kind, period.prev_anchor))
        if any(r.entries_count for r in prev_rows):
            prev_rank = {r.class_id: r.rank for r in _assign_ranks(prev_rows)}
            for row in ranked:
                row.change = prev_rank[row.class_id] - row.rank if row.class_id in prev_rank else None
    return ranked


def criterion_breakdown(db: Session, period: Period, class_id: int | None = None) -> list[CriterionRow]:
    conditions = [ScoreEntry.criterion_id == Criterion.id,
                  ScoreEntry.entry_date.between(period.start, period.end)]
    if class_id:
        conditions.append(ScoreEntry.class_id == class_id)
    pos = func.coalesce(func.sum(case((ScoreEntry.points > 0, ScoreEntry.points), else_=0)), 0)
    neg = func.coalesce(func.sum(case((ScoreEntry.points < 0, ScoreEntry.points), else_=0)), 0)
    stmt = (
        select(Criterion.id, Criterion.name, pos, neg, func.count(ScoreEntry.id))
        .select_from(Criterion)
        .outerjoin(ScoreEntry, and_(*conditions))
        .where(Criterion.is_active.is_(True))
        .group_by(Criterion.id)
        .order_by(Criterion.id)
    )
    return [CriterionRow(cid, name, round(p, 2), round(n, 2), cnt) for cid, name, p, n, cnt in db.execute(stmt).all()]


def weekly_trend(db: Session, weeks: int = 8, anchor: date | None = None, top_n: int = 5) -> dict:
    """Điểm ròng theo từng tuần của `top_n` lớp có tổng cao nhất trong khoảng quan sát."""
    anchor = anchor or date.today()
    last_monday = anchor - timedelta(days=anchor.weekday())
    starts = [last_monday - timedelta(weeks=i) for i in range(weeks - 1, -1, -1)]
    range_start, range_end = starts[0], last_monday + timedelta(days=6)

    names = {c.id: c.name for c in db.scalars(select(SchoolClass).where(SchoolClass.is_active.is_(True)))}
    series = {cid: [0.0] * weeks for cid in names}
    rows = db.execute(
        select(ScoreEntry.class_id, ScoreEntry.entry_date, ScoreEntry.points)
        .where(ScoreEntry.entry_date.between(range_start, range_end))
    ).all()
    for cid, day, points in rows:
        if cid in series:
            series[cid][(day - range_start).days // 7] += points

    top = sorted(series, key=lambda cid: -sum(series[cid]))[:top_n]
    return {
        "labels": [f"{s:%d/%m}" for s in starts],
        "datasets": [{"label": names[cid], "data": [round(v, 2) for v in series[cid]]} for cid in top],
    }
