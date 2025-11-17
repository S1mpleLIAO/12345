import logging

_logger = None


def get_logger(name: str = "mcp"):
    global _logger
    if _logger is None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        )
        _logger = logging.getLogger(name)
    return _logger
