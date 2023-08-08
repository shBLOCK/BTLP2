import binascii
import io
import logging
import asyncio
import json
import base64
import PIL
from PIL import Image
import websockets
from websockets.legacy.server import WebSocketServerProtocol

import utils
import worker


class ClientHandlingException(Exception):
    def __init__(self, cause: str, extra_data: dict = None):
        self.cause = cause
        self.extra_data = extra_data or {}

class Server:
    def __init__(self):
        self.pool = worker.WorkerPool(
            self._on_queue_update,
            self._on_progress,
            self._on_result
        )

        self._clients: list[WebSocketServerProtocol, ...] = []

    @staticmethod
    async def send(conns: WebSocketServerProtocol | list[WebSocketServerProtocol, ...], event: str, msg: dict):
        msg_json = json.dumps({"event": event, "data": msg}, ensure_ascii=False)
        if type(conns) is not list:
            conns = [conns]

        for conn in conns:
            await conn.send(msg_json)
    # noinspection PyMethodMayBeStatic
    async def _handle(self, conn: WebSocketServerProtocol):
        logging.info(f"Accepted client: {conn.remote_address}")
        self._clients.append(conn)

        while True:
            try:
                msg_raw = await conn.recv()
                try:
                    msg = json.loads(msg_raw)
                except json.JSONDecodeError as e:
                    logging.warning(f"Failed to parse client message: {e}\n{msg_raw}")
                    continue
                logging.debug(f"Received {msg}")

                try:
                    await self._handle_client_message(conn, msg)
                except Exception as e:
                    logging.exception(f"An uncaught exception occurred when handling client message: {msg}", e)
            except websockets.WebSocketException as e:
                logging.info(f"Client disconnected: {e}")
                break
        
        self.pool.on_client_disconnect(conn)
        self._clients.remove(conn)

    async def _handle_client_message(self, conn: WebSocketServerProtocol, msg: dict):
        event = msg.get("event")
        if event is None:
            logging.warning(f"Client message didn't defined the event type: {msg}")
            return
        data = msg.get("data", {})

        if event == "submit":
            try:
                await self._handle_submission(conn, data)
            except ClientHandlingException as e:
                logging.warning(f"Failed to handle submission: {e.cause} {e.extra_data}")
                await self.send(conn, "submit_fail", {"cause": e.cause, **e.extra_data})

    async def _handle_submission(self, conn: WebSocketServerProtocol, data: dict):
        request_id = data.get("id")
        prompt = data.get("prompt")
        image = data.get("image")
        image_width = data.get("image_width")
        image_height = data.get("image_height")
        args = data.get("args", {})

        error_extras = {} if request_id is None else {"id": request_id}
        if type(request_id) is not int or\
            type(prompt) is not str or\
            type(image) is not str or\
            type(image_width) is not int or\
            type(image_height) is not int or\
            type(args) is not dict:
            raise ClientHandlingException(
                "Invalid id, prompt, image or args.",
                error_extras
            )

        try:
            image = base64.b64decode(image, validate=True)
            image = Image.frombytes("RGBA", (image_width, image_height), image).convert("RGB")
        except (binascii.Error, PIL.UnidentifiedImageError) as e:
            raise ClientHandlingException(f"Failed to load image: {e}", error_extras)

        work = worker.Work(conn, request_id, prompt, image, args)
        logging.info(f"Submitting work: {prompt}")
        await self.pool.submit(work)

    async def _on_queue_update(self, queue):
        await self.send(self._clients, "queue_len", {"len": len(queue)})

        for i, work in enumerate(queue):
            await self.send(work.client, "queue_pos", {"id": work.request_id, "pos": i})

    async def _on_progress(self, _, work, progress):
        await self.send(work.client, "progress", {"id": work.request_id, "progress": progress})

    async def _on_result(self, _, work, result):
        await self.send(work.client, "result", {"id": work.request_id, "result": result})

    async def main(self):
        async with websockets.serve(self._handle, "localhost", 8001):
            while True:
                await self.pool.update()
                await asyncio.sleep(0.01)


if __name__ == '__main__':
    utils.configure_logger(logging.getLogger())
    server = Server()
    asyncio.run(server.main())
