
from rich.logging import RichHandler
import logging

logging.basicConfig(
    level="NOTSET",
    format="| %(message)s",
    datefmt="%X",
    handlers=[RichHandler(rich_tracebacks=True)],
)

def test_logger():
    logger = logging.getLogger("test_logger")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

if __name__ == "__main__":
    test_logger()