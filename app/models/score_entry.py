from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScoreEntry(Base):
    """Một lần cộng/trừ điểm. points > 0 là cộng, points < 0 là trừ."""
    __tablename__ = "score_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    criterion_id: Mapped[int] = mapped_column(ForeignKey("criteria.id"), index=True)
    points: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    school_class = relationship("SchoolClass", back_populates="entries", lazy="joined")
    criterion = relationship("Criterion", back_populates="entries", lazy="joined")
    author = relationship("User", lazy="joined")
