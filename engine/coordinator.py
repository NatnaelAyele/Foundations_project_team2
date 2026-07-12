"""
Main orchestration engine for the Tomato Logistics Platform.

This module coordinates the entire logistics workflow by calling
each processing module in sequence.
"""

import traceback
from datetime import datetime

from validator import Validator
from eligibility import EligibilityChecker
from clustering import ClusteringEngine
from demand import DemandAnalyzer
from truck_matcher import TruckMatcher
from hub_matcher import HubMatcher
from planner import Planner
from reservation import ReservationManager
from notifier import Notifier
from logger import EngineLogger


class CoordinationEngine:
    """
    Coordinates the complete logistics pipeline.
    """

    def __init__(self):

        self.validator = Validator()

        self.eligibility = EligibilityChecker()

        self.clustering = ClusteringEngine()

        self.demand = DemandAnalyzer()

        self.truck_matcher = TruckMatcher()

        self.hub_matcher = HubMatcher()

        self.planner = Planner()

        self.reservation = ReservationManager()

        self.notifier = Notifier()

        self.logger = EngineLogger()

    def run(self):

        start_time = datetime.now()
        plan = None
        notifications = None

        self.logger.info("Starting coordination engine...")
        self.logger.info(f"Coordination engine started at {start_time}.")

        try:

            self.logger.info("Creating coordination plan...")
            plan = self.create_coordination_plan()

            self.logger.info("Loading pending forecasts...")
            pending_forecasts = self.load_pending_forecasts()

            self.logger.info("Validating forecasts...")
            valid_forecasts = self.validator.validate(
                pending_forecasts
            )

            self.logger.info("Checking eligibility...")
            eligible_forecasts = self.eligibility.filter(
                valid_forecasts
            )

            self.logger.info("Creating clusters...")
            clusters = self.clustering.create_clusters(
                eligible_forecasts
            )

            self.logger.info("Calculating demand...")
            demand_results = self.demand.calculate(
                clusters
            )

            self.logger.info("Matching trucks...")
            truck_matches = self.truck_matcher.match(
                demand_results
            )

            self.logger.info("Matching hubs...")
            hub_matches = self.hub_matcher.match(
                truck_matches
            )

            self.logger.info("Creating trip allocations...")
            planning_results = self.planner.plan_trips(
                plan["plan_id"],
                hub_matches
            )

            self.logger.info("Reserving resources...")
            reservations = self.reservation.reserve(
                planning_results
            )

            self.logger.info("Sending notifications...")
            notifications = self.notifier.create_notifications(
                reservations
            )

            self.logger.info("Completing coordination plan...")
            self.complete_coordination_plan(plan)

            self.logger.info("Coordination plan completed successfully.")
            self.logger.info("Coordination engine completed successfully.")

            return {
                "status": "success",
                "plan": plan,
                "notifications": notifications
            }

        except Exception as error:

            self.logger.error(f"Coordination engine failed: {error}")
            self.logger.error(traceback.format_exc())

            if plan is not None:
                self.fail_plan(plan)

            return {
                "status": "failed",
                "error": str(error)
            }
        finally:

            end_time = datetime.now()
            duration = end_time - start_time

            self.logger.info(f"Coordination engine finished at {end_time}.")
            self.logger.info(f"Coordination engine execution duration: {duration}.")

    def create_coordination_plan(self):
        """
        Create a temporary coordination plan.

        Later, the service layer can replace this with a real database record.
        """
        return {
            "plan_id": 1,
            "status": "RUNNING",
            "generated_at": datetime.now()
        }

    def load_pending_forecasts(self):
        """
        Load pending forecasts.

        """
        return []

    def complete_coordination_plan(self, plan):
        """Mark the temporary coordination plan as completed."""
        plan["status"] = "COMPLETED"
        plan["completed_at"] = datetime.now()
        return plan

    def fail_plan(self, plan):
        """Mark the temporary coordination plan as failed."""
        plan["status"] = "FAILED"
        plan["failed_at"] = datetime.now()
        return plan
