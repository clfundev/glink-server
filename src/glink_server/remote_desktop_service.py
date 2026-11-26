import asyncio
import json
import logging
import platform
import socket

import pyautogui
import pyperclip
from websockets.asyncio.server import ServerConnection, serve

from .screen_grabber import ScreenGrabber

WEBSOCKET_PORT = 8765

# 指令类型
LEFT_CLICK = "lclick"
RIGHT_CLICK = "rclick"
DOUBLE_LEFT_CLICK = "dlclick"
SCROLL = "scroll"
KEYBOARD_INPUT = "key"
TEXT_INPUT = "text"

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = False

screen_grabber = ScreenGrabber()


# 执行来自客户端的控制指令
def execute_command(command_json: str) -> None:
    try:
        logger.info(f"Execute command: {command_json}")
        command = json.loads(command_json)
        command_type = command["type"]
        if command_type == LEFT_CLICK:
            x_ratio = command["xRatio"]
            y_ratio = command["yRatio"]
            screen_width, screen_height = pyautogui.size()
            x = int(x_ratio * screen_width)
            y = int(y_ratio * screen_height)
            pyautogui.leftClick(x, y)
            logger.info(f"Left click ({x}, {y})")
        elif command_type == RIGHT_CLICK:
            x_ratio = command["xRatio"]
            y_ratio = command["yRatio"]
            screen_width, screen_height = pyautogui.size()
            x = int(x_ratio * screen_width)
            y = int(y_ratio * screen_height)
            pyautogui.rightClick(x, y)
            logger.info(f"Right click ({x}, {y})")
        elif command_type == DOUBLE_LEFT_CLICK:
            x_ratio = command["xRatio"]
            y_ratio = command["yRatio"]
            screen_width, screen_height = pyautogui.size()
            x = int(x_ratio * screen_width)
            y = int(y_ratio * screen_height)
            pyautogui.doubleClick(x, y)
            logger.info(f"Double left click ({x}, {y})")
        elif command_type == SCROLL:
            amount = command["amount"]
            pyautogui.scroll(amount)
            logger.info(f"Scroll {amount}")
        elif command_type == KEYBOARD_INPUT:
            key_name = command["keyName"]
            pyautogui.press(key_name)
            logger.info(f"Press key [{key_name}]")
        elif command_type == TEXT_INPUT:
            text = command["text"]
            type(text)
            logger.info(f"Input text [{text}]")
    except Exception:
        logger.exception("Execute command error")


# 通过复制粘贴实现文本输入
def type(text: str):
    pyperclip.copy(text)
    if platform.system() == "Darwin":
        pyautogui.hotkey("command", "v")
    else:
        pyautogui.hotkey("ctrl", "v")


# 处理WebSocket连接
async def handle_client(websocket: ServerConnection):
    logger.info(f"Client [{websocket.id}] connected")
    try:
        await screen_grabber.register(websocket)
        async for message in websocket:
            if isinstance(message, str):
                await asyncio.get_event_loop().run_in_executor(
                    None, execute_command, message
                )
    except Exception:
        logger.exception("WebSocket connection error")
    finally:
        await screen_grabber.unregister(websocket)
        logger.info(f"Client [{websocket.id}] disconnected")


async def run_remote_desktop_service():
    logger.info(
        f"WebSocket server started on ws://{socket.gethostbyname(socket.gethostname())}:{WEBSOCKET_PORT}"
    )
    async with serve(handle_client, "", WEBSOCKET_PORT):
        await asyncio.Event().wait()
