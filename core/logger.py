# core/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO
LOG_FILE = "logs/app.log"

def init_logger():
    # 根日志器
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(LOG_FORMAT)

    # 控制台日志
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 文件日志，最大5MB，保留5个备份
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # 避免重复添加 handler
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    # 第三方库日志等级
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # 可以调整为 INFO 查看访问日志
