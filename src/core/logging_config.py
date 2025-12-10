# Custom logging configuration for FastAPI

import logging
import logging.config
from pathlib import Path

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging(log_level: str = "INFO"):
    """
    Setup custom logging configuration.

    Args:
    Args:
        log_level: Overrides the log level in logging.ini if provided (optional logic can be added)
    """
    config_path = Path("logging.ini")

    if config_path.exists():
        logging.config.fileConfig(config_path, disable_existing_loggers=False)
        logging.info("Logging configuration loaded from logging.ini")
    else:
        # Fallback if logging.ini is missing
        logging.basicConfig(level=log_level)
        logging.warning("logging.ini not found, using basic config")

    return logging.getLogger("src")


# Get application logger
logger = logging.getLogger("src")


# Custom log formatter with colors (for terminal)
class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    COLORS = {
        logging.DEBUG: grey,
        logging.INFO: blue,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno)
        formatter = logging.Formatter(
            f"{log_color}%(asctime)s | %(levelname)-8s | %(name)s | %(message)s{self.reset}",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return formatter.format(record)
