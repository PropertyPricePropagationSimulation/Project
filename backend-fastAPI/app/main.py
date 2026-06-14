from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.routers import register_routers

app = FastAPI(
    title="SSAFY Home Backend",
    version="0.1.0",
    description="부동산 정책 충격 전파 분석 시스템"
)

register_routers(app)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    event_window_content = openapi_schema["paths"]["/analysis/event-window"]["post"][
        "requestBody"
    ]["content"]["application/json"]
    event_window_content["example"] = {
        "event_id": 30,
        "window_months": 3,
        "region_codes": None,
    }
    event_window_content["examples"]["all_regions"]["value"]["region_codes"] = None

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
