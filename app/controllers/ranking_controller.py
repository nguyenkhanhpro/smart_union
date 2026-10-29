from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.templating import render
from app.database import get_db
from app.models import User
from app.services.period import period_from_params
from app.services.ranking_service import get_ranking

router = APIRouter(prefix="/rankings")


@router.get("")
def index(request: Request, kind: str = "week", date: str | None = None,
          user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    period = period_from_params(kind, date)
    return render(request, "rankings/index.html", {"period": period, "ranking": get_ranking(db, period, with_change=True)})
