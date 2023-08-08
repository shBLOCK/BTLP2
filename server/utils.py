import logging
import sys


def configure_logger(logger: logging.Logger):
    formatter = logging.Formatter("%(asctime)s [%(name)s %(levelname)s] %(message)s")

    console_hdl = logging.StreamHandler(sys.stdout)
    console_hdl.setFormatter(formatter)
    console_hdl.addFilter(lambda log: log.levelno <= logging.INFO)
    logger.addHandler(console_hdl)

    console_hdl_err = logging.StreamHandler(sys.stderr)
    console_hdl_err.setFormatter(formatter)
    console_hdl_err.setLevel(logging.WARNING)
    logger.addHandler(console_hdl_err)
    
    file_hdl = logging.FileHandler("latest.log")
    file_hdl.setFormatter(formatter)
    file_hdl.setLevel(logging.INFO)
    logger.addHandler(file_hdl)

    logger.setLevel(logging.INFO)
