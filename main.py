from fastapi import FastAPI
from api.routes import router as api_router
import uvicorn
from core.config import SERVER_CONFIG
from core.logger import init_logger
from scheduler.task_runner import start_scheduler
# 初始化日志
init_logger()
app = FastAPI()
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    import logging
    logging.getLogger(__name__).info("Scheduler 启动完成")


if __name__ == "__main__":
    uvicorn.run("main:app", **SERVER_CONFIG)