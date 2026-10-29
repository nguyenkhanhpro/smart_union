from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.core.templating import render
from app.database import get_db
from app.models import User
from app.services.score_service import list_history

router = APIRouter(prefix="/history")


@router.get("")
def index(request: Request, page: int = 1, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows, total = list_history(db, page)
    pages = max((total + settings.PER_PAGE - 1) // settings.PER_PAGE, 1)
    return render(request, "history/index.html", {"rows": rows, "total": total, "page": page, "pages": pages, "qs": ""})
