"""
Main orchestration engine for the Tomato Logistics Platform.

This module coordinates the entire logistics workflow by calling
each processing module in sequence.
"""

import traceback
from datetime import datetime

try:

    from backend.engine_group1.pipeline import (
        ClusteringEngine,
        DemandAnalyzer,
        EligibilityChecker,
        Validator,
        read_pending_forecasts,
    )
except ImportError as error:
    raise ImportError(
        "Could not import Group 1 pipeline classes from "
        "backend.engine_group1.pipeline. Check that backend/engine_group1 "
        "is a Python package and that pipeline.py is available."
    ) from error

try:

    from engine.logger import EngineLogger
    from engine.notifier import Notifier
    from engine.payment import PaymentManager
    from engine.planner import Planner
    from engine.reservation import ReservationManager
except ImportError:

    from logger import EngineLogger
    from notifier import Notifier
    from payment import PaymentManager
    from planner import Planner
    from reservation import ReservationManager


class CoordinationEngine:
    """
    Coordinates the complete logistics pipeline.

    The coordinator exists to call each engine module in the correct order. It
    receives an optional database session and an optional coordination plan
    dictionary. When a real service layer is added, that service should create
    the database plan first and pass the saved plan here.
    """

    def __init__(self, db=None, logger=None, coordination_plan=None):

        self.db = db
        self.initial_coordination_plan = coordination_plan

        self.logger = logger or EngineLogger()

        self.validator = Validator()

        self.eligibility = EligibilityChecker()

        self.clustering = ClusteringEngine()

        self.demand = DemandAnalyzer()

        self.truck_matcher = None

        self.hub_matcher = None

        self.planner = Planner(logger=self.logger)

        self.reservation = ReservationManager(logger=self.logger)

        self.payment = PaymentManager(logger=self.logger)

        self.notifier = Notifier(logger=self.logger)

    def run(self, coordination_plan=None):
        """
        Run the full engine workflow and return a summary dictionary.

        Receives an optional persisted coordination plan. Returns success data
        with plan, payment, and notification results, or a failed status with a
        readable error message.
        """

        start_time = datetime.now()
        plan = None
        notifications = None

        self.logger.info("Starting coordination engine...")
        self.logger.info(f"Coordination engine started at {start_time}.")

        try:

            self.logger.info("Creating coordination plan...")
            plan = self.create_coordination_plan(coordination_plan)

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
            if demand_results:
                truck_matches = self.get_truck_matcher().match(
                    demand_results
                )
            else:
                truck_matches = []

            self.logger.info("Matching hubs...")
            if truck_matches:
                hub_matches = self.get_hub_matcher().match(
                    truck_matches
                )
            else:
                hub_matches = []

            successful_matches = self.get_successful_matches(hub_matches)

            self.logger.info("Creating trip allocations...")
            planning_results = self.planner.plan_trips(
                plan.get("plan_id"),
                successful_matches
            )
            planning_results = self.attach_match_context_to_trips(
                planning_results,
                successful_matches
            )

            self.logger.info("Reserving resources...")
            reservations = self.reservation.reserve(
                planning_results
            )

            self.logger.info("Initializing payments...")
            payment_results = self.payment.initialize_payment(
                reservations
            )

            self.logger.info("Sending notifications...")
            notifications = self.notifier.create_notifications(
                payment_results
            )

            self.logger.info("Completing coordination plan...")
            self.complete_coordination_plan(plan)

            self.logger.info("Coordination plan completed successfully.")
            self.logger.info("Coordination engine completed successfully.")

            return {
                "status": "success",
                "plan": plan,
                "payments": payment_results,
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

    def create_coordination_plan(self, coordination_plan=None):
        """
        Return a real or temporary coordination plan dictionary.

        Receives a plan from the caller when database persistence already
        created one.
        """
        plan = coordination_plan or self.initial_coordination_plan

        if plan:
            normalized_plan = plan.copy()
            normalized_plan.setdefault("status", "RUNNING")
            normalized_plan.setdefault("generated_at", datetime.now())
            normalized_plan.setdefault("temporary_engine_state", False)
            return normalized_plan

        return {
            # The database will generate the real integer plan_id later.
            "plan_id": None,
            "temporary_plan_key": f"TEMP-PLAN-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "status": "RUNNING",
            "generated_at": datetime.now(),
            "temporary_engine_state": True,
            "persistence_status": "PENDING_DATABASE_INSERT",
            "persistence_notes": (
                "The service layer should insert coordination_plans first, "
                "then pass the generated plan_id back into this coordinator."
            ),
        }

    def load_pending_forecasts(self):
        """
        Load pending forecasts using Group 1's real pipeline reader.

        A database session is required for real Sprint 2 data. If no session
        is provided, this method returns an empty list as a temporary demo
        state that can be replaced by service-layer database logic later.
        """
        if self.db is None:
            self.logger.warning(
                "No database session provided. Pending forecast loading "
                "is using temporary demo data."
            )
            return []

        return read_pending_forecasts(self.db)

    def get_successful_matches(self, hub_matches):
        """
        Return only matches that can be planned.

        Group 2 may return excluded entries when no truck or hub is available.
        Planner should receive only successful matches.
        """
        return [
            match
            for match in hub_matches
            if not match.get("excluded")
        ]

    def get_truck_matcher(self):
        """
        Create or return Group 2's TruckMatcher.

        The import happens here so missing model dependencies produce a clear
        error only when truck matching is actually needed.
        """
        if self.truck_matcher is None:
            TruckMatcher, _ = self.import_group2_matchers()
            self.truck_matcher = TruckMatcher(self.db)

        return self.truck_matcher

    def get_hub_matcher(self):
        """
        Create or return Group 2's HubMatcher.

        The coordinator uses this class for hub matching and does not duplicate
        Group 2's matching logic.
        """
        if self.hub_matcher is None:
            _, HubMatcher = self.import_group2_matchers()
            self.hub_matcher = HubMatcher(self.db)

        return self.hub_matcher

    def import_group2_matchers(self):
        """
        Import Group 2 matcher classes.

        Returns TruckMatcher and HubMatcher from backend.engine2, or raises a
        clear ImportError when their package or model dependencies are missing.
        """
        try:

            from backend.engine2.hub_matcher import HubMatcher
            from backend.engine2.truck_matcher import TruckMatcher
        except ImportError as error:
            raise ImportError(
                "Could not import Group 2 matchers from backend.engine2. "
                "Check that backend/engine2 is a Python package and that "
                "Truck, ColdHub, Transporter, and User models are importable."
            ) from error

        return TruckMatcher, HubMatcher

    def attach_match_context_to_trips(self, planning_results, successful_matches):
        """
        Add match context needed by later engine steps.

        Planner creates the trip fields, while this method keeps contact and
        forecast data from Group 2 available for reservation, payment, and
        notifications.
        """
        trip_allocations = planning_results.get("trip_allocations", [])
        enriched_trips = []

        for index, trip in enumerate(trip_allocations):
            enriched_trip = trip.copy()

            if index < len(successful_matches):
                match = successful_matches[index]
                cluster = match.get("cluster", {})
                forecasts = cluster.get("forecasts", [])

                enriched_trip["cluster"] = cluster
                enriched_trip["forecasts"] = forecasts
                enriched_trip["farmer_phones"] = [
                    forecast.get("farmer_phone")
                    for forecast in forecasts
                    if forecast.get("farmer_phone")
                ]

                if enriched_trip["farmer_phones"]:
                    enriched_trip["farmer_phone"] = enriched_trip[
                        "farmer_phones"
                    ][0]

                enriched_trip["transporter_phone"] = match.get(
                    "transporter_phone"
                )
                enriched_trip["hub_phone"] = match.get("hub_phone")
                enriched_trip["admin_phone"] = match.get("admin_phone")

            enriched_trips.append(enriched_trip)

        enriched_results = planning_results.copy()
        enriched_results["trip_allocations"] = enriched_trips
        return enriched_results

    def complete_coordination_plan(self, plan):
        """
        Mark the coordination plan as completed in engine memory.

        Receives a plan dictionary and returns it with completion fields. The
        future service layer should persist this status to coordination_plans.
        """
        plan["status"] = "COMPLETED"
        plan["completed_at"] = datetime.now()
        return plan

    def fail_plan(self, plan):
        """
        Mark the coordination plan as failed in engine memory.

        Receives a plan dictionary and returns it with failure fields. The
        future service layer should persist this status to coordination_plans.
        """
        plan["status"] = "FAILED"
        plan["failed_at"] = datetime.now()
        return plan
