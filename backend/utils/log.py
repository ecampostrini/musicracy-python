"""This modules defines project-wise logging utilities"""

import logging


def get_logger(name="nameless_logger"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] %(message)s')

    if not logger.handlers:
        fh = logging.FileHandler("%s.log" % name)
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
