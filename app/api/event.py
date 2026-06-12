from fastapi import APIRouter, HTTPException, Query

from app.schemas import EventCreate
from app.services import event_service

router = APIRouter()


@router.post("/")
async def create_event(payload: EventCreate):
    return event_service.create_event(payload.model_dump())


@router.get("/")
async def list_events():
    return event_service.list_events()


@router.get("/json")
async def list_events_json(
    include_details: bool = Query(True, description="Include type-specific event detail data."),
):
    return event_service.list_events_json(include_details=include_details)


@router.put("/{event_id}")
async def update_event(event_id: int, payload: EventCreate):
    result = event_service.update_event(event_id, payload.model_dump())
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Event not found.")
    return result


@router.delete("/{event_id}")
async def delete_event(event_id: int):
    result = event_service.delete_event(event_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Event not found.")
    return result
