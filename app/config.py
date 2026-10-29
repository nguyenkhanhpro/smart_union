"""Cấu hình tập trung. Đổi giá trị qua biến môi trường khi triển khai."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


class Settings:
    APP_NAME = "Smart Union AI"
    SECRET_KEY = os.getenv("SECRET_KEY", "doi-chuoi-bi-mat-nay-khi-trien-khai")
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'smart_union.db'}")
    # Điểm gốc mỗi lớp trong một kỳ thi đua (0 = chỉ tính tổng điểm cộng/trừ).
    BASE_SCORE = float(os.getenv("BASE_SCORE", "0"))
    PER_PAGE = 20


settings = Settings()
