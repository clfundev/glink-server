import asyncio
import json
import logging
import socket

from .remote_desktop_service import WEBSOCKET_PORT

DISCOVERY_PORT = 7420
DISCOVERY_MESSAGE = "Who is GlinkServer?"

logger = logging.getLogger(__name__)


class ServerInfo:
    def __init__(self, id: str, address: str, name: str):
        self.id = id
        self.address = address
        self.name = name


class AutoDiscoveryProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            msg = data.decode("utf-8")
        except UnicodeDecodeError:
            logger.info(f"Received non-UTF8 data from {addr}, ignored")
            return

        if DISCOVERY_MESSAGE not in msg:
            logger.info(f"Received non-discovery message [{msg}] from {addr}, ignored")
            return

        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            server_info = ServerInfo(
                hostname.lower(), f"ws://{ip}:{WEBSOCKET_PORT}", hostname
            )
            response = json.dumps(server_info.__dict__)
            logger.info(
                f"Received discovery message [{msg}] from {addr}, responding with {response}"
            )
            self.transport.sendto(response.encode("utf-8"), addr)
        except Exception:
            logger.exception("respond error")

    def error_received(self, exc):
        logger.error(f"UDP error received: {exc}")


async def listen_for_auto_discovery_message(address: str = "0.0.0.0"):
    try:
        transport, _ = await asyncio.get_event_loop().create_datagram_endpoint(
            AutoDiscoveryProtocol,
            local_addr=(address, DISCOVERY_PORT),
            allow_broadcast=True,
        )
    except Exception:
        logger.exception(f"Unable to bind {address}:{DISCOVERY_PORT}")
        return

    logger.info(f"Listening for auto-discovery messages on {address}:{DISCOVERY_PORT}")
    try:
        await asyncio.Event().wait()
    finally:
        transport.close()


async def run_auto_discovery_service():
    await listen_for_auto_discovery_message()
