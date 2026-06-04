from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.shared.database.session import get_session
from app.shared.common.response import success_response, error_response
from app.shared.common.exceptions import BusinessException
from app.modules.visualization.service import VisualizationService

router = APIRouter(tags=["visualization"])
service = VisualizationService()


@router.get("/api/visualization-data/{task_id}", response_model=dict)
def get_visualization_data(
    task_id: str,
    session: Session = Depends(get_session),
):
    try:
        result = service.get_visualization_data(session, task_id)
        return success_response("Visualization data loaded.", data=result.model_dump())
    except BusinessException as e:
        status_code = {
            "VISUALIZATION_PREREQUISITES_MISSING": 404,
            "VISUALIZATION_DATA_MISSING": 404,
        }.get(e.error_code, 400)
        raise HTTPException(status_code=status_code, detail=error_response(e.message, error_code=e.error_code))
