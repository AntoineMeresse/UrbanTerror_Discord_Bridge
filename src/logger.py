import logging
import logging.handlers
import os


def setup_logger():
    root = logging.getLogger("bridge")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)s: %(message)s", datefmt="%H:%M:%S")

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    os.makedirs("logs", exist_ok=True)
    fh = logging.handlers.TimedRotatingFileHandler(
        "logs/bridge.log", when="midnight", backupCount=7, encoding="utf-8"
    )
    fh.setLevel(logging.WARNING)
    fh.setFormatter(fmt)
    root.addHandler(fh)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"bridge.{name}")
