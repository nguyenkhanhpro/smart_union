"""Kỳ thi đua: tuần / tháng / học kỳ.

Quy ước học kỳ (sửa tại đây nếu quy chế trường khác):
  - Học kỳ 1: 01/09 – 31/01
  - Học kỳ 2: 01/02 – 31/08
"""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta

KINDS = {"week": "Tuần", "month": "Tháng", "semester": "Học kỳ"}


@dataclass(frozen=True)
class Period:
    kind: str
    start: date
    end: date
    label: str

    @property
    def prev_anchor(self) -> date:
        return self.start - timedelta(days=1)

    @property
    def next_anchor(self) -> date:
        return self.end + timedelta(days=1)

    @property
    def is_current(self) -> bool:
        return self.start <= date.today() <= self.end


def resolve_period(kind: str, anchor: date) -> Period:
    if kind == "month":
        last_day = calendar.monthrange(anchor.year, anchor.month)[1]
        return Period(kind, anchor.replace(day=1), anchor.replace(day=last_day),
                      f"Tháng {anchor.month}/{anchor.year}")

    if kind == "semester":
        if anchor.month >= 9:
            year, sem = anchor.year, 1
        elif anchor.month == 1:
            year, sem = anchor.year - 1, 1
        else:
            year, sem = anchor.year - 1, 2
        if sem == 1:
            start, end = date(year, 9, 1), date(year + 1, 1, 31)
        else:
            start, end = date(year + 1, 2, 1), date(year + 1, 8, 31)
        return Period(kind, start, end, f"Học kỳ {sem}, năm học {year}–{year + 1}")

    start = anchor - timedelta(days=anchor.weekday())
    end = start + timedelta(days=6)
    return Period("week", start, end, f"Tuần {start.isocalendar().week}: {start:%d/%m} – {end:%d/%m/%Y}")


def period_from_params(kind: str | None, date_str: str | None) -> Period:
    """Đọc tham số URL an toàn; sai định dạng thì rơi về tuần hiện tại."""
    kind = kind if kind in KINDS else "week"
    try:
        anchor = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        anchor = date.today()
    return resolve_period(kind, anchor)
