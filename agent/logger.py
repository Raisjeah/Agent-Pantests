import logging
from rich.logging import RichHandler

class AILogger:
    def __init__(self, name="ai-pentest"):
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[RichHandler(rich_tracebacks=True)]
        )
        self.logger = logging.getLogger(name)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
