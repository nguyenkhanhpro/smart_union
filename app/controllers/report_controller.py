from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.templating import render
from app.database import get_db
from app.models import User
from app.services import report_service
from app.services.period import period_from_params

router = APIRouter(prefix="/reports")


@router.get("")
def index(request: Request, kind: str = "week", date: str | None = None,
          user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    period = period_from_params(kind, date)
    return render(request, "reports/index.html", {"period": period, "report": report_service.build_report(db, period)})


@router.get("/export.xlsx")
def export_xlsx(kind: str = "week", date: str | None = None,
                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    period = period_from_params(kind, date)
    content = report_service.export_excel(db, period)
    filename = f"bao-cao-{period.kind}-{period.start.isoformat()}.xlsx"
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
