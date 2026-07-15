"""
Logging utility for the Tomato Logistics Platform.

This is a simple logger that can be shared across
the coordination engine modules.
"""

import logging


class EngineLogger:
    """Simple logger used by all engine modules."""

    def __init__(self):
        self.logger = logging.getLogger("TomatoLogisticsEngine")

        # Prevent duplicate log handlers
        if not self.logger.handlers:

            self.logger.setLevel(logging.INFO)

            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)

    def info(self, message):
        """Log an informational message."""
        self.logger.info(message)

    def warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message):
        """Log an error message."""
        self.logger.error(message)

    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)

    def critical(self, message):
        """Log a critical error message."""
        self.logger.critical(message)