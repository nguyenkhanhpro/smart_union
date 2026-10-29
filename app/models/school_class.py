from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SchoolClass(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True)
    grade: Mapped[int] = mapped_column(Integer, index=True)
    school_year: Mapped[str] = mapped_column(String(15))
    homeroom_teacher: Mapped[str] = mapped_column(String(100), default="")
    note: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    entries = relationship("ScoreEntry", back_populates="school_class")
