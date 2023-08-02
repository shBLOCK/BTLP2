import logging
import asyncio
import websockets
from websockets.legacy.server import WebSocketServerProtocol


async def handle(conn: WebSocketServerProtocol):
    logging.info(f"Accepted client: {conn.remote_address}")

    while True:
        try:
            msg = await conn.recv()
            logging.debug(f"Received {msg}")
        except Exception as e:
            logging.info(f"Client disconnected: {e}")
            return

async def main():
    async with websockets.serve(handle, "localhost", 8001):
        await asyncio.Future()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO
    )
    import worker
    pool = worker.WorkerPool()
    # asyncio.run(main())
