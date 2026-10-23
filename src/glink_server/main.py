import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from .auto_discovery_service import run_auto_discovery_service
from .remote_desktop_service import run_remote_desktop_service

# 确保日志文件夹存在
os.makedirs("logs", exist_ok=True)

# 全局日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    handlers=[
        RotatingFileHandler(
            "logs/glink_server.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)


# 启动自动发现服务和远程桌面服务
async def run_service():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_auto_discovery_service())
        tg.create_task(run_remote_desktop_service())


def main():
    asyncio.run(run_service())


if __name__ == "__main__":
    main()
