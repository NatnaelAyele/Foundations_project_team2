"""
scheduler.py

Simple scheduler for the Tomato Logistics Platform.

This module is responsible for starting the coordination engine.
It can be run manually during development and later replaced by
a real scheduler such as APScheduler or Celery.
"""

from coordinator import CoordinationEngine
from logger import EngineLogger


class Scheduler:
    """Runs the coordination engine."""

    def __init__(self):
        self.engine = CoordinationEngine()
        self.logger = EngineLogger()

    def run(self):
        """
        Start the coordination engine.
        """

        self.logger.info("Scheduler started.")

        try:
            result = self.engine.run()

            self.logger.info("Scheduler completed successfully.")

            return result

        except Exception as error:

            self.logger.error(f"Scheduler failed: {error}")

            raise


def main():
    """
    Entry point for running the scheduler manually.
    """

    scheduler = Scheduler()
    scheduler.run()


if __name__ == "__main__":
    main()