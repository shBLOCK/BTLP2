import logging
import sys


def configure_logger(logger: logging.Logger):
    formatter = logging.Formatter("%(asctime)s [%(name)s| %(levelname)s] %(message)s")
    console_hdl = logging.StreamHandler(sys.stdout)
    console_hdl.setFormatter(formatter)
    logger.addHandler(console_hdl)
    logger.setLevel(logging.INFO)
