"""Kiểm chứng phép tính điểm, xếp hạng và kỳ thi đua bằng dữ liệu nhỏ tính tay được."""
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Criterion, SchoolClass, ScoreEntry, User
from app.services.period import resolve_period
from app.services.ranking_service import criterion_breakdown, get_ranking


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        session.add(User(id=1, username="t", full_name="GV", password_hash="x"))
        session.add_all([SchoolClass(id=i, name=n, grade=6, school_year="2026-2027")
                         for i, n in enumerate(["6A", "6B", "6C", "6D"], start=1)])
        session.add_all([Criterion(id=1, name="Vệ sinh"), Criterion(id=2, name="Nề nếp")])
        session.commit()
        yield session


def add(db, class_id, points, day=date(2026, 10, 28), criterion_id=1):
    db.add(ScoreEntry(class_id=class_id, criterion_id=criterion_id, points=points, reason="test",
                      entry_date=day, created_by=1))
    db.commit()


def test_total_and_rank(db):
    add(db, 1, 5); add(db, 1, -2)      # 6A = 3
    add(db, 2, 10)                     # 6B = 10
    add(db, 3, -4)                     # 6C = -4
    rows = {r.class_name: r for r in get_ranking(db, resolve_period("week", date(2026, 10, 28)))}
    assert (rows["6B"].rank, rows["6B"].total) == (1, 10)
    assert (rows["6A"].rank, rows["6A"].total, rows["6A"].positive, rows["6A"].negative) == (2, 3, 5, -2)
    assert rows["6D"].total == 0 and rows["6D"].rank == 3   # lớp chưa có điểm vẫn có mặt
    assert rows["6C"].rank == 4


def test_tie_same_rank_competition_style(db):
    add(db, 1, 5); add(db, 2, 5); add(db, 3, 1)
    ranks = sorted((r.rank for r in get_ranking(db, resolve_period("week", date(2026, 10, 28)))))
    assert ranks == [1, 1, 3, 4]   # 1-1-3-4 (6D = 0 xếp cuối)


def test_tie_broken_by_fewer_penalties(db):
    add(db, 1, 8); add(db, 1, -3)      # 6A: 5 điểm, bị trừ 3
    add(db, 2, 5)                      # 6B: 5 điểm, không bị trừ
    rows = {r.class_name: r.rank for r in get_ranking(db, resolve_period("week", date(2026, 10, 28)))}
    assert rows["6B"] == 1 and rows["6A"] == 2


def test_period_filtering(db):
    add(db, 1, 5, date(2026, 10, 26))   # thứ Hai
    add(db, 1, 3, date(2026, 11, 1))    # Chủ nhật
    add(db, 1, 100, date(2026, 11, 2))  # tuần sau
    week = {r.class_name: r.total for r in get_ranking(db, resolve_period("week", date(2026, 10, 29)))}
    month = {r.class_name: r.total for r in get_ranking(db, resolve_period("month", date(2026, 10, 29)))}
    assert week["6A"] == 8 and month["6A"] == 5


def test_rank_change_vs_previous_period(db):
    add(db, 1, 5, date(2026, 10, 20)); add(db, 2, 9, date(2026, 10, 20))    # tuần trước: 6B hạng 1
    add(db, 1, 9, date(2026, 10, 27)); add(db, 2, 5, date(2026, 10, 27))    # tuần này: 6A hạng 1
    rows = {r.class_name: r for r in get_ranking(db, resolve_period("week", date(2026, 10, 29)), with_change=True)}
    assert rows["6A"].change == 1 and rows["6B"].change == -1


def test_criterion_breakdown(db):
    add(db, 1, 5, criterion_id=1); add(db, 1, -2, criterion_id=2); add(db, 2, -1, criterion_id=2)
    period = resolve_period("week", date(2026, 10, 28))
    all_rows = {r.name: r for r in criterion_breakdown(db, period)}
    assert all_rows["Nề nếp"].negative == -3 and all_rows["Vệ sinh"].positive == 5
    only_6a = {r.name: r for r in criterion_breakdown(db, period, class_id=1)}
    assert only_6a["Nề nếp"].negative == -2


@pytest.mark.parametrize("anchor,label_part,start,end", [
    (date(2026, 10, 29), "Học kỳ 1", date(2026, 9, 1), date(2027, 1, 31)),
    (date(2027, 1, 15), "Học kỳ 1", date(2026, 9, 1), date(2027, 1, 31)),
    (date(2027, 3, 10), "Học kỳ 2", date(2027, 2, 1), date(2027, 8, 31)),
])
def test_semester(anchor, label_part, start, end):
    p = resolve_period("semester", anchor)
    assert label_part in p.label and (p.start, p.end) == (start, end)


def test_week_runs_monday_to_sunday():
    p = resolve_period("week", date(2026, 10, 29))  # thứ Năm
    assert (p.start, p.end) == (date(2026, 10, 26), date(2026, 11, 1))
