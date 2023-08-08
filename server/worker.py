import logging
import multiprocessing
from multiprocessing import Process, Pipe
import enum
import asyncio

import PIL
from PIL import Image
import torch

import config
import utils


##### DEBUG SECTION START #####
DEBUGGING = False
if DEBUGGING:
    from time import sleep
    from random import random

if not DEBUGGING:
    import model_api

class DummyModel:
    # noinspection PyMissingConstructor
    def __init__(self):
        pass

    def generate(
            self,
            prompt: str,
            image: torch.Tensor,
            use_nucleus_sampling=False,
            num_beams=5,
            max_length=30,
            min_length=1,
            top_p=0.9,
            repetition_penalty=1.0,
            length_penalty=1.0,
            num_captions=1,
            temperature=1,
    ):
        for i in range(3):
            yield f"progress {i+1}"
            sleep(random())
        return ["DUMMY RESULT"]

def _debug_load_model():
    sleep(random() * 3)
    return DummyModel()
##### DEBUG SECTION END #####

class MsgType(enum.Enum):
    PENDING = enum.auto()
    PROGRESS = enum.auto()
    RESULT = enum.auto()


def _worker_func(pipe, name: str, device_name: str):
    logger: logging.Logger = multiprocessing.get_logger()
    logger.name = name
    utils.configure_logger(logger)

    logger.info(f"Loading with device: {device_name}")

    if not DEBUGGING:
        device = torch.device(device_name)
        model = model_api.load_model(device)
    else:
        model = _debug_load_model()

    logger.info("Loading completed, waiting for tasks...")

    gen_cnt = 0
    while True:
        pipe.send((MsgType.PENDING, None))
        work = pipe.recv()

        logger.info(f"Starting generation {gen_cnt}...\nPrompt: {work.prompt}\nImage(size): {work.image.size}\nArgs: {work.args}")

        generator = model.generate(work.prompt, work.image, **work.args)
        while True:
            try:
                progress = next(generator)
                logger.info(f"Generation {gen_cnt} progress: {progress}")
                pipe.send((MsgType.PROGRESS, progress))
            except StopIteration as si:
                logger.info(f"Generation {gen_cnt} completed:\n" + "\n".join(si.value))
                gen_cnt += 1
                pipe.send((MsgType.RESULT, si.value))
                break


class Worker:
    def __init__(self, pool: "WorkerPool", name: str, device: str, progress_callback, result_callback):
        self.pool = pool
        self._progress_callback = progress_callback
        self._result_callback = result_callback

        multiprocessing.set_start_method("spawn", True)
        self._pipe, _proc_pipe = Pipe()
        _proc = Process(target=_worker_func, args=(_proc_pipe, name, device), name=name)
        _proc.start()
        logging.info(f"Worker process starting: {name}")

        self._initializing = True
        self._busy = True
        self._work = None

    @property
    def busy(self):
        return self._busy

    async def submit(self, work):
        await self.update()
        assert not self.busy, "This worker is still busy."

        self._pipe.send(work)
        self._busy = True
        self._work = work

    async def update(self):
        """
        Call this method regularly!
        """
        while self._pipe.poll():
            msg, data = self._pipe.recv()
            if msg == MsgType.PENDING:
                self._busy = False
            elif msg == MsgType.PROGRESS:
                await self._progress_callback(self, self._work, data)
            elif msg == MsgType.RESULT:
                await self._result_callback(self, self._work, data)
            else:
                assert False


class Work:
    def __init__(self, client, request_id: int, prompt: str, image: PIL.Image, args: dict):
        self.client = client
        self.request_id = request_id

        self.prompt = prompt
        self.image = image
        self.args = args
    
    def __getstate__(self):
        return {
            "request_id": self.request_id,
            "prompt": self.prompt,
            "image": self.image,
            "args": self.args
        }


class WorkerPool:
    def __init__(self, queue_update_callback, progress_callback, result_callback):
        self._workers = []

        for i, device_name in enumerate(config.WORKERS):
            self._workers.append(Worker(
                self,
                f"Worker {i}",
                device_name,
                progress_callback,
                result_callback
            ))

        self._work_queue = []

        self._queue_update_callback = queue_update_callback

    @property
    def queue(self):
        return tuple(self._work_queue)

    async def submit(self, work: Work):
        self._work_queue.append(work)
        await self._queue_update_callback(self.queue)

    def on_client_disconnect(self, client):
        self._work_queue = [w for w in self._work_queue if w.client == client]

    async def update(self):
        """
        Call this regularly!
        """

        for w in self._workers:
            await w.update()

        while len(self._work_queue) > 0:
            for w in self._workers:
                if not w.busy:
                    work = self._work_queue.pop(0)
                    print(work, work.client, work.request_id, work.prompt, work.image, work.args)
                    await w.submit(work)
                    await self._queue_update_callback(self.queue)
                    break
            else:
                break


if __name__ == '__main__':
    utils.configure_logger(logging.getLogger())
    logging.basicConfig()

    def on_queue_update(queue):
        logging.warning(f"Queue update: {len(queue)}")

    def on_progress(worker, work, progress):
        logging.warning(f"Progress: {work} {progress}")

    def on_result(worker, work, result):
        logging.warning(f"Progress: {work} {result}")

    pool = WorkerPool(on_queue_update, on_progress, on_result)

    for i in range(17):
        path = f"../img_prompt/{i+1:02d}/"
        prompt = open(path + "prompt.txt").read().strip()
        image = Image.open(path + "img.jpg").convert("RGB")
        image = path + "img.jpg"
        pool.submit(Work(
            None, 1, prompt, image, {}
        ))

    # for i in range(17):
    #     prompt = f"prompt {i}"
    #     image = None
    #     pool.submit(Work(
    #         None, 1, prompt, image, {}
    #     ))

    async def test():
        while True:
            pool.update()
            await asyncio.sleep(0)

    asyncio.run(test())
