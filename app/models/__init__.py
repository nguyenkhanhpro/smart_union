from app.models.criterion import Criterion
from app.models.school_class import SchoolClass
from app.models.score_entry import ScoreEntry
from app.models.score_history import ScoreHistory
from app.models.user import ROLE_ADMIN, ROLE_TEACHER, User

__all__ = [
    "User", "SchoolClass", "Criterion", "ScoreEntry", "ScoreHistory",
    "ROLE_ADMIN", "ROLE_TEACHER",
]
