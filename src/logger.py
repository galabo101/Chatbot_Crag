import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


# === Config ===
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(name)-28s | %(levelname)-7s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Max 5MB per file, keep 3 backups
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True
) -> logging.Logger:

    logger = logging.getLogger(name)

    # Tránh duplicate handlers khi import nhiều lần
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (rotating)
    if log_to_file:
        log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
