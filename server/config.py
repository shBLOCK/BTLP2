from torch import device


WORKERS = (
    *(f"cuda:{i}" for i in range(4, 7)),
)

MODEL_NAME = "blip2_opt"
MODEL_TYPE = "pretrain_opt2.7b"
