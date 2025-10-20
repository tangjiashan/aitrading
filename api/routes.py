import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/send_message")
def send_message_to_teregram():

    # logger.info(f"接收到需要发送的 {request.message} ")

    return {"message": "send message successful"}

