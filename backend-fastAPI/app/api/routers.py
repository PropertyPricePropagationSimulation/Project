from fastapi import FastAPI
from app.api.collect import router as collect_router
from app.api.preprocess import router as preprocess_router
from app.api.event import router as event_router
from app.api.analysis import router as analysis_router
from app.api.batch import router as batch_router


def register_routers(app: FastAPI) -> None:
    app.include_router(collect_router, prefix="/collect", tags=["데이터 수집"])
    app.include_router(batch_router, prefix="/api/batch", tags=["배치"])
    app.include_router(preprocess_router, prefix="/preprocess", tags=["전처리"])
    app.include_router(event_router, prefix="/events", tags=["이벤트"])
    app.include_router(analysis_router, prefix="/analysis", tags=["분석"])
