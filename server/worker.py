import logging
import multiprocessing
from multiprocessing import Process, Pipe
import enum

import torch

import config
import utils

##### DEBUG SECTION START #####
DEBUGGING = __name__ == "__main__" or __name__ == "__mp_main__"
if DEBUGGING:
    from time import sleep
    import asyncio
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

        logger.info(f"Starting generation {gen_cnt}...\nPrompt: {work.prompt}\nImage: {work.image}\nArgs: {work.args}")

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
    def __init__(self, name: str, device: str):
        self._pipe, _proc_pipe = Pipe()
        _proc = Process(target=_worker_func, args=(_proc_pipe, name, device), name=name)
        _proc.start()
        logging.info(f"Worker process starting: {name}")

        self._initializing = True
        self._busy = True

    @property
    def busy(self):
        return self._busy

    def submit(self, work):
        self.update()
        assert not self.busy, "This worker is still busy."

        self._pipe.send(work)
        self._busy = True

    def update(self):
        """
        Call this method regularly!
        """
        while self._pipe.poll():
            msg, data = self._pipe.recv()
            if msg == MsgType.PENDING:
                self._busy = False
            elif msg == MsgType.PROGRESS:
                pass
            elif msg == MsgType.RESULT:
                pass
            else:
                assert False


class Work:
    def __init__(self, client, prompt, image, args):
        self.client = client

        self.prompt = prompt
        self.image = image
        self.args = args


class WorkerPool:
    def __init__(self):
        self._workers = []

        for i, device_name in enumerate(config.WORKERS):
            self._workers.append(Worker(
                f"Worker {i}",
                device_name
            ))

        self._work_queue = []

    @property
    def queue_length(self):
        return len(self._work_queue)

    def submit(self, work: Work):
        self._work_queue.append(work)

    def on_client_disconnect(self, client):
        self._work_queue = [w for w in self._work_queue if w.client == client]

    def update(self):
        """
        Call this regularly!
        """

        for w in self._workers:
            w.update()

        while len(self._work_queue) > 0:
            for w in self._workers:
                if not w.busy:
                    w.submit(self._work_queue.pop(0))
                    break
            else:
                break


if __name__ == '__main__':
    utils.configure_logger(logging.getLogger())
    logging.basicConfig()

    logging.getLogger().info("test")

    pool = WorkerPool()

    for i in range(30):
        pool.submit(Work(
            None, f"test {i} prompt", None, {"max_length": 100}
        ))

    async def test():
        while True:
            pool.update()
            await asyncio.sleep(0)

    asyncio.run(test())
