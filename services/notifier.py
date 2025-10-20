import logging

import requests
from core.config import PROXY_ADDRESS
from dotenv import load_dotenv
import os
load_dotenv()  # 自动读取 .env 文件
logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# 全局代理

def send_telegram(message: str) -> bool:
        """
        发送 Telegram 消息到群组或个人。
        :param message: 要发送的消息内容
        :return: True if success, False otherwise
        """
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = {
            'chat_id': CHAT_ID,
            'text': message
        }
        try:
            resp = requests.post(url, data=data, proxies={"https": PROXY_ADDRESS}, timeout=10)
            resp.raise_for_status()
            logger.info(f"Send telegram message successful, code: {resp.status_code}")
            return True
        except Exception as e:
            logger.info(f"[Telegram Error] {e}")
            return False

def send_discord(message: str) -> bool:
        """
        发送消息到 Discord webhook。
        :param message: 要发送的消息内容
        :return: True if success, False otherwise
        """
        data = {
            'content': message
        }

        try:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=data, proxies={"https": PROXY_ADDRESS}, timeout=10)
            resp.raise_for_status()
            logger.info(f"Send discord message successful, code: {resp.status_code}")
            return True
        except Exception as e:
            logger.info(f"[Discord Error] {e}")
            return False

