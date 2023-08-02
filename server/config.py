from torch import device


WORKERS = (
    *(f"cuda:{i}" for i in range(10)),
)

MODEL_NAME = "blip2_opt"
MODEL_TYPE = "pretrain_opt2.7b"
