import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class NullLogger:
    def debug(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None


def build_scan_logger(sim_cfg: dict, logging_cfg: dict | None):
    log_level = str(sim_cfg.get("log_level", "INFO")).upper()
    if log_level != "DEBUG":
        return NullLogger()

    cfg = logging_cfg or {}
    path = Path(cfg.get("file_path", "logs/simulator_debug.log"))
    max_bytes = int(cfg.get("max_bytes", 1024 * 1024))
    backup_count = int(cfg.get("backup_count", 5))

    path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("kvsim.scan")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers.clear()

    handler = RotatingFileHandler(
        filename=path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
