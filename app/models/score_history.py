import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

ACTION_LABELS = {"create": "Thêm", "update": "Sửa", "delete": "Xóa"}


class ScoreHistory(Base):
    """Nhật ký thay đổi điểm. Không khóa ngoại tới score_entries để vẫn giữ lại khi bản ghi bị xóa."""
    __tablename__ = "score_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_id: Mapped[int | None] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(10))
    old_data: Mapped[str | None] = mapped_column(Text)
    new_data: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

    user = relationship("User", lazy="joined")

    @property
    def action_label(self) -> str:
        return ACTION_LABELS.get(self.action, self.action)

    @property
    def old(self) -> dict | None:
        return json.loads(self.old_data) if self.old_data else None

    @property
    def new(self) -> dict | None:
        return json.loads(self.new_data) if self.new_data else None
