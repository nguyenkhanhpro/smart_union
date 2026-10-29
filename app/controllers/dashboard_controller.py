from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.templating import render
from app.database import get_db
from app.models import User
from app.services.period import period_from_params
from app.services.ranking_service import criterion_breakdown, get_ranking, weekly_trend

router = APIRouter()


@router.get("/")
def dashboard(request: Request, kind: str = "week", date: str | None = None,
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    period = period_from_params(kind, date)
    ranking = get_ranking(db, period, with_change=True)
    return render(request, "dashboard/index.html", {
        "period": period,
        "ranking": ranking,
        "podium": ranking[:3] if any(r.entries_count for r in ranking) else [],
        "class_count": len(ranking),
        "entries_count": sum(r.entries_count for r in ranking),
        "total_positive": round(sum(r.positive for r in ranking), 2),
        "total_negative": round(sum(r.negative for r in ranking), 2),
    })


# --- Dữ liệu JSON cho biểu đồ (component chart-card.js gọi các endpoint này) ---
@router.get("/api/dashboard/trend")
def api_trend(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return JSONResponse(weekly_trend(db))


@router.get("/api/dashboard/criteria")
def api_criteria(kind: str = "week", date: str | None = None, class_id: int | None = None,
                 user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = criterion_breakdown(db, period_from_params(kind, date), class_id)
    return JSONResponse({
        "labels": [r.name for r in rows],
        "positive": [r.positive for r in rows],
        "negative": [r.negative for r in rows],
    })
