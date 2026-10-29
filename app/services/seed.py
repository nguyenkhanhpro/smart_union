"""Dữ liệu mẫu để chạy thử (chỉ chạy khi CSDL còn trống)."""
import random
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import ROLE_ADMIN, ROLE_TEACHER, Criterion, SchoolClass, User
from app.services import score_service

CRITERIA = {
    "Vệ sinh": ("Vệ sinh lớp học và khu vực được phân công",
                ["Lớp sạch, rác được phân loại", "Khu vực hành lang gọn gàng"],
                ["Rác chưa đổ sau giờ học", "Bảng chưa lau", "Khu vực được giao còn bẩn"]),
    "Nề nếp": ("Truy bài, xếp hàng, trật tự, chuyên cần",
               ["Xếp hàng nhanh, trật tự", "Truy bài đúng giờ"],
               ["Nói chuyện riêng trong giờ truy bài", "Đi học muộn", "Xếp hàng chậm"]),
    "Học tập": ("Điểm tốt, chuẩn bị bài, phong trào học tập",
                ["Nhiều điểm 10 trong tuần", "Phát biểu xây dựng bài tốt"],
                ["Không làm bài tập về nhà", "Thiếu sách vở"]),
    "Đồng phục": ("Đồng phục, khăn quàng, huy hiệu",
                  ["Cả lớp đeo khăn quàng đầy đủ"],
                  ["Quên khăn quàng", "Không mặc đồng phục đúng quy định"]),
    "Hoạt động Đội": ("Sinh hoạt Đội, phong trào, văn nghệ, thể thao",
                      ["Tham gia tích cực hội thi văn nghệ", "Sinh hoạt chi đội nghiêm túc"],
                      ["Vắng sinh hoạt Đội không phép"]),
}
CLASS_NAMES = ["6A", "6B", "6C", "7A", "7B", "7C", "8A", "8B", "8C", "9A", "9B", "9C"]
TEACHERS = ["Nguyễn Thị Lan", "Trần Văn Minh", "Lê Thu Hà", "Phạm Quốc Bảo", "Hoàng Mai Anh", "Vũ Đức Thành"]


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(func.count(User.id))):
        return
    admin = User(username="admin", full_name="Quản trị Liên đội", role=ROLE_ADMIN, password_hash=hash_password("admin123"))
    teacher = User(username="giaovien", full_name="Nguyễn Thị Lan", role=ROLE_TEACHER, password_hash=hash_password("gv123456"))
    db.add_all([admin, teacher])

    today = date.today()
    year = today.year if today.month >= 9 else today.year - 1
    school_year = f"{year}-{year + 1}"
    classes = [SchoolClass(name=n, grade=int(n[0]), school_year=school_year, homeroom_teacher=TEACHERS[i % len(TEACHERS)])
               for i, n in enumerate(CLASS_NAMES)]
    criteria = [Criterion(name=n, description=d[0]) for n, d in CRITERIA.items()]
    db.add_all(classes + criteria)
    db.commit()

    rng = random.Random(2026)
    monday = today - timedelta(days=today.weekday())
    for weeks_back in range(6):
        week_start = monday - timedelta(weeks=weeks_back)
        for cls in classes:
            for _ in range(rng.randint(2, 4)):
                crit = rng.choice(criteria)
                positive = rng.random() < 0.45
                reasons = CRITERIA[crit.name][1 if positive else 2]
                day = min(week_start + timedelta(days=rng.randint(0, 4)), today)
                points = rng.choice([1, 2, 3, 5])
                score_service.create_entry(db, teacher, {
                    "class_id": cls.id, "criterion_id": crit.id,
                    "points": points if positive else -points,
                    "reason": rng.choice(reasons), "entry_date": day,
                })
