import asyncio
import contextlib
import ctypes
import logging

import cv2
import dxcam
import numpy as np
import win32api
import win32con
import win32gui
import win32process
import win32ui
from PIL import Image
from websockets.asyncio.server import ServerConnection

logger = logging.getLogger(__name__)


class ScreenGrabber:
    def __init__(self, fps=20, quality=100):
        self._fps: int = fps
        self._quality: int = quality
        self._clients: set[ServerConnection] = set()
        self._task: asyncio.Task | None = None
        self._cam: dxcam.DXCamera | None = None  # 非空表示ScreenGrabber已启动
        self._lock = asyncio.Lock()

    async def register(self, ws: ServerConnection):
        async with self._lock:
            self._clients.add(ws)
            await self._start()

    async def unregister(self, ws: ServerConnection):
        async with self._lock:
            self._clients.discard(ws)
            # 无客户端时停止屏幕捕获、释放资源
            if not self._clients:
                await self._stop()

    async def _start(self):
        if self._cam is None:
            self._cam = dxcam.create(output_color='RGBA')
            self._cam.start(target_fps=self._fps)
            self._task = asyncio.create_task(self._run())
        else:
            logger.info("ScreenGrabber has already started")

    async def _stop(self):
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task  # 等待任务真正结束
            self._task = None
        if self._cam is not None:
            self._cam.stop()
            self._cam.release()
            self._cam = None

    async def _run(self):
        try:
            while True:
                # 获取屏幕截图
                screenshot = await asyncio.get_event_loop().run_in_executor(None, self._get_screenshot)
                if screenshot is None:
                    continue
                # 将屏幕截图发送给所有客户端
                if not self._clients:
                    continue
                await asyncio.gather(
                    *(self._safe_send(ws, screenshot) for ws in self._clients),
                    return_exceptions=True,
                )
        except Exception:
            logger.exception("ScreenGrabber _run() error")

    async def _safe_send(self, ws: ServerConnection, data) -> bool:
        try:
            await ws.send(data)
            return True
        except Exception:
            return False

    # 屏幕截图补充绘制光标
    def _draw_cursor(self, screen_img: Image.Image):
        self._print_gdi_count()
        hbmp = None
        hdc = None
        hdc_origin = None

        try:
            # 创建画布
            hdc_origin = win32gui.GetDC(0)
            hdc = win32ui.CreateDCFromHandle(hdc_origin)
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, 36, 36)
            hdc = hdc.CreateCompatibleDC()
            hdc.SelectObject(hbmp)

            # 获取光标并将其绘制到画布上
            hcursor = win32gui.GetCursorInfo()[1]
            hdc.DrawIcon((0, 0), hcursor)

            # 将光标位图转换成PIL Image
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            cursor_img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1).convert("RGBA")

            # 将纯黑且不透明的像素改为透明
            pixels = cursor_img.load()
            if pixels is not None:
                width, height = cursor_img.size
                for y in range(height):
                    for x in range(width):
                        if pixels[x, y] == (0, 0, 0, 255):
                            pixels[x, y] = (0, 0, 0, 0)

            # 获取光标位置、热点、比例
            cursor_pos = win32gui.GetCursorPos()
            ratio = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
            _, hotspot_x, hotspot_y, _, _ = win32gui.GetIconInfo(hcursor)  # type: ignore
            paste_x = round(cursor_pos[0] * ratio - hotspot_x)
            paste_y = round(cursor_pos[1] * ratio - hotspot_y)

            # 将光标粘贴到屏幕截图上
            screen_img.paste(cursor_img, (paste_x, paste_y), cursor_img)
        except Exception:
            logger.exception("Failed to draw cursor")
        finally:
            # 资源释放
            if hbmp is not None:
                win32gui.DeleteObject(hbmp.GetHandle())
            if hdc is not None:
                hdc.DeleteDC()
            if hdc_origin is not None:
                win32gui.ReleaseDC(0, hdc_origin)

    # 对dxcam屏幕截图补充绘制光标、进行JPEG编码
    def _process_frame(self, frame: np.ndarray) -> bytes:
        img = Image.fromarray(frame, mode='RGBA')

        self._draw_cursor(img)
        img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
        _, buffer = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, self._quality])
        return buffer.tobytes()

    # 获取处理过的屏幕截图
    def _get_screenshot(self) -> bytes | None:
        if self._cam is None:
            return
        frame = self._cam.get_latest_frame()
        if frame is None:
            return
        return self._process_frame(frame)

    # 日志打印GDI对象数，若持续上涨，说明_draw_cursor()中的资源没有正确释放
    def _print_gdi_count(self):
        pid = win32api.GetCurrentProcessId()
        h_process = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        try:
            gdi_count = win32process.GetGuiResources(h_process, win32con.GR_GDIOBJECTS)
            logger.debug(f"PID: {pid}, current GDI object count: {gdi_count}")
        finally:
            win32api.CloseHandle(h_process)
