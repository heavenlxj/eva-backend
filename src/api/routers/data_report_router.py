from core.middleware import skip_client_verification_for_router
from fastapi import APIRouter, BackgroundTasks, Request
from typing import List
from loguru import logger
from core.rabbitmq import RabbitMQClient
from entity.base import BaseResponse
from entity.data_track import TrackEventRequest

rabbitmq = RabbitMQClient()

api_router = skip_client_verification_for_router(
    APIRouter(prefix="/data", tags=["auth"])
)


def get_client_ip(request: Request) -> str:
    """Get client real IP address"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    logger.debug(f"Forwarded for: {forwarded_for}")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    logger.debug(f"Real IP: {real_ip}")
    if real_ip:
        return real_ip

    return request.client.host if request.client else ""


@api_router.post("/tracking")
async def tracking_events(
    events: List[TrackEventRequest], background_tasks: BackgroundTasks, request: Request
):
    client_ip = get_client_ip(request)
    for event in events:
        if event.extra is None:
            event.extra = {}
        event.extra["client_ip"] = client_ip

    logger.info(
        f"Received data tracking request, event details: {[event.model_dump() for event in events]}"
    )
    background_tasks.add_task(rabbitmq.publish_events, events)
    return BaseResponse.success("OK")
