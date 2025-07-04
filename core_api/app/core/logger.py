import logging


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    setup_logger()
    return logging.getLogger(name)
