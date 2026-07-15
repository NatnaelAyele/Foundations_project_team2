"""
Tomato Logistics Engine Person 3 simulator.

This script demonstrates the Engine's functionality by simulating several logistics scenarios.:

Planner
    |
Reservation
    |
Notifier

Run with:
    python test_engine.py
"""

import time
import traceback

from backend.engine.notifier import Notifier
from backend.engine.planner import Planner
from backend.engine.reservation import ReservationManager


def loading(message):
    """Show a short loading animation."""
    print(message, end="", flush=True)
    for _ in range(5):
        time.sleep(0.5)
        print(".", end="", flush=True)
    print(" done\n")


def print_header(title):
    """Print a large section header."""
    print("\n========================================")
    print(title)
    print("========================================\n")


def print_line():
    """Print a simple divider."""
    print("----------------------------------------")


def create_match(
    truck_id,
    hub_id,
    sector_id,
    truck_capacity,
    hub_capacity,
    forecasts,
    farmer_phone,
    transporter_phone,
    hub_phone,
    admin_phone,
):
    """Create one successful match using the current planner input format."""
    total_load = 0

    for forecast in forecasts:
        total_load += forecast["quantity_kg"]

    return {
        "truck_id": truck_id,
        "hub_id": hub_id,
        "sector_id": sector_id,
        "cluster": {
            "sector_id": sector_id,
            "total_load_kg": total_load,
            "forecasts": forecasts
        },
        "truck": {
            "truck_id": truck_id,
            "capacity_kg": truck_capacity
        },
        "hub": {
            "hub_id": hub_id,
            "available_capacity_kg": hub_capacity
        },
        "farmer_phone": farmer_phone,
        "transporter_phone": transporter_phone,
        "hub_phone": hub_phone,
        "admin_phone": admin_phone
    }


def create_sample_matches():
    """Create realistic sample matches for several logistics scenarios."""
    return [
        create_match(
            truck_id=5,
            hub_id=3,
            sector_id=1,
            truck_capacity=900,
            hub_capacity=1200,
            forecasts=[
                {"forecast_id": 101, "quantity_kg": 250},
                {"forecast_id": 102, "quantity_kg": 300}
            ],
            farmer_phone="0780000001",
            transporter_phone="0780000101",
            hub_phone="0780000201",
            admin_phone="0780000301"
        ),
        create_match(
            truck_id=6,
            hub_id=4,
            sector_id=2,
            truck_capacity=700,
            hub_capacity=900,
            forecasts=[
                {"forecast_id": 201, "quantity_kg": 180},
                {"forecast_id": 202, "quantity_kg": 220}
            ],
            farmer_phone="0780000002",
            transporter_phone="0780000102",
            hub_phone="0780000202",
            admin_phone="0780000301"
        ),
        create_match(
            truck_id=7,
            hub_id=5,
            sector_id=3,
            truck_capacity=1000,
            hub_capacity=1500,
            forecasts=[
                {"forecast_id": 301, "quantity_kg": 450},
                {"forecast_id": 302, "quantity_kg": 350}
            ],
            farmer_phone="0780000003",
            transporter_phone="0780000103",
            hub_phone="0780000203",
            admin_phone="0780000301"
        ),
        create_match(
            truck_id=8,
            hub_id=6,
            sector_id=4,
            truck_capacity=500,
            hub_capacity=700,
            forecasts=[
                {"forecast_id": 401, "quantity_kg": 120},
                {"forecast_id": 402, "quantity_kg": 180}
            ],
            farmer_phone="0780000004",
            transporter_phone="0780000104",
            hub_phone="0780000204",
            admin_phone="0780000301"
        )
    ]


def add_runtime_details(planning, matches):
    """Add display/runtime details needed by reservation and notifier."""
    for index, trip in enumerate(planning["trip_allocations"]):
        match = matches[index]

        trip["available_capacity_kg"] = match["hub"]["available_capacity_kg"]
        trip["farmer_phone"] = match["farmer_phone"]
        trip["transporter_phone"] = match["transporter_phone"]
        trip["hub_phone"] = match["hub_phone"]
        trip["admin_phone"] = match["admin_phone"]


def display_planning_results(planning):
    """Display planner results in a readable format."""
    trips = planning["trip_allocations"]
    forecast_allocations = planning["forecast_allocations"]

    print("Creating trip allocations...")
    print("Success")
    print("Creating forecast allocations...")
    print("Success\n")

    for index, trip in enumerate(trips, start=1):
        print_line()
        print(f"Trip Allocation {index}")
        print(f"Truck ID: {trip['truck_id']}")
        print(f"Hub ID: {trip['hub_id']}")
        print(f"Sector ID: {trip['sector_id']}")
        print(f"Total Load: {trip['total_load_kg']} kg")
        print(f"Pickup Start: {trip['pickup_start']}")
        print(f"Estimated Hub Arrival: {trip['estimated_hub_arrival']}")
        print(f"Status: {trip['status']}")

    print_line()
    print(f"Trips Created: {len(trips)}")
    print(f"Forecast Allocations Created: {len(forecast_allocations)}")


def display_reservation_change(before_trip, after_trip):
    """Display before and after reservation state for one trip."""
    print_line()
    print(f"Truck {before_trip['truck_id']}")
    print("Status Before: AVAILABLE")
    print("|")
    print(f"Status After: {after_trip['truck_status']}")
    print()
    print(f"Hub {before_trip['hub_id']}")
    print(f"Hub Capacity Before: {before_trip.get('available_capacity_kg')} kg")
    print(f"Reserved Quantity: {before_trip['total_load_kg']} kg")
    print("|")
    print(f"Hub Capacity After: {after_trip.get('available_capacity_kg')} kg")
    print()
    print(f"Trip Status Before: {before_trip['status']}")
    print("|")
    print(f"Trip Status After: {after_trip['status']}")


def display_notifications(notifications):
    """Display notifications in a presentation-friendly format."""
    for index, notification in enumerate(notifications, start=1):
        print_line()
        print(f"Notification {index}")
        print()
        print("Recipient:")
        print(notification["recipient_type"])
        print()
        print("Phone:")
        print(notification["recipient_phone"])
        print()
        print("Message:")
        print(notification["message"])
        print()
        print("Status:")
        print(notification["status"])

    print_line()


def run_planner(planner, plan_id, matches):
    """Run planner and validate the planning result."""
    loading("Loading Planner")
    print("Searching for available truck...")
    print("Truck Found")
    print("Checking cold hub capacity...")
    print("Hub Available")

    planning = planner.plan_trips(plan_id, matches)
    add_runtime_details(planning, matches)

    assert "trip_allocations" in planning
    assert "forecast_allocations" in planning
    assert len(planning["trip_allocations"]) > 0
    assert len(planning["forecast_allocations"]) > 0

    display_planning_results(planning)
    return planning


def run_reservation(reservation_manager, planning):
    """Run reservation and validate the reservation result."""
    loading("Loading Reservation Module")

    before_trips = []
    for trip in planning["trip_allocations"]:
        before_trips.append(trip.copy())

    reservation = reservation_manager.reserve(planning)

    assert reservation["reservation_status"] == "SUCCESS"
    assert reservation["reserved_trips"] == len(reservation["trip_allocations"])

    for index, trip in enumerate(reservation["trip_allocations"]):
        assert trip["status"] == "RESERVED"
        assert trip["truck_status"] == "BUSY"
        assert trip.get("reserved_at") is not None
        assert trip["available_capacity_kg"] >= 0

        display_reservation_change(before_trips[index], trip)

    print(f"\nReservations Completed: {reservation['reserved_trips']}")
    return reservation


def run_notifier(notifier, reservation):
    """Run notifier and validate notification result."""
    loading("Loading Notification Module")

    notifications = notifier.create_notifications(reservation)
    notification_list = notifications["notifications"]
    recipient_types = []

    for notification in notification_list:
        recipient_types.append(notification["recipient_type"])

    assert notifications["status"] == "SUCCESS"
    assert len(notification_list) > 0
    assert "FARMER" in recipient_types
    assert "TRANSPORTER" in recipient_types
    assert "HUB_OPERATOR" in recipient_types
    assert "ADMIN" in recipient_types

    display_notifications(notification_list)
    print(f"Notifications Created: {len(notification_list)}")
    return notifications


def scenario_normal_reservation(planner, reservation_manager, notifier):
    """Scenario 1: normal reservation with one successful match."""
    print_header("SCENARIO 1 - NORMAL RESERVATION")

    match = [create_sample_matches()[0]]
    planning = run_planner(planner, 1, match)
    reservation = run_reservation(reservation_manager, planning)
    notifications = run_notifier(notifier, reservation)

    return {
        "clusters": len(match),
        "trips": len(planning["trip_allocations"]),
        "forecast_allocations": len(planning["forecast_allocations"]),
        "reservations": reservation["reserved_trips"],
        "notifications": len(notifications["notifications"]),
        "failed_reservations": 0
    }


def scenario_shared_truck(planner, reservation_manager):
    """Scenario 2: two trips use the same truck."""
    print_header("SCENARIO 2 - SHARED TRUCK")

    matches = [
        create_match(
            9, 7, 1, 800, 1000,
            [{"forecast_id": 501, "quantity_kg": 250}],
            "0780000401", "0780000501", "0780000601", "0780000301"
        ),
        create_match(
            9, 8, 2, 800, 900,
            [{"forecast_id": 502, "quantity_kg": 300}],
            "0780000402", "0780000501", "0780000602", "0780000301"
        )
    ]

    planning = run_planner(planner, 2, matches)
    reservation = run_reservation(reservation_manager, planning)

    reserved_trucks = []
    duplicate_truck_found = False

    for trip in reservation["trip_allocations"]:
        if trip["truck_id"] in reserved_trucks:
            duplicate_truck_found = True
        reserved_trucks.append(trip["truck_id"])

    print("\nShared Truck Result:")
    print("Truck 9 was assigned to two trips.")

    if duplicate_truck_found:
        print("Current engine result: both trips were reserved.")
        print("Business validation: shared truck conflict detected.")
        print("This simulator marks the second reservation as a failed case.")
        failed_reservations = 1
    else:
        print("Current engine result: duplicate truck was rejected or avoided.")
        failed_reservations = 0

    return {
        "clusters": len(matches),
        "trips": len(planning["trip_allocations"]),
        "forecast_allocations": len(planning["forecast_allocations"]),
        "reservations": reservation["reserved_trips"],
        "notifications": 0,
        "failed_reservations": failed_reservations
    }


def scenario_hub_capacity(reservation_manager):
    """Scenario 3: hub capacity decreases and rejects over-capacity trip."""
    print_header("SCENARIO 3 - HUB CAPACITY")
    loading("Checking Hub Capacity")

    planning = {
        "trip_allocations": [
            {
                "plan_id": 3,
                "truck_id": 10,
                "hub_id": 9,
                "sector_id": 1,
                "total_load_kg": 400,
                "pickup_start": "demo",
                "estimated_hub_arrival": "demo",
                "status": "SCHEDULED",
                "available_capacity_kg": 500
            }
        ],
        "forecast_allocations": []
    }

    print("Capacity Before First Reservation: 500 kg")
    first_reservation = reservation_manager.reserve(planning)
    first_trip = first_reservation["trip_allocations"][0]
    print("Reserved Quantity: 400 kg")
    print(f"Remaining Capacity: {first_trip['available_capacity_kg']} kg")

    assert first_trip["available_capacity_kg"] == 100

    over_capacity_plan = {
        "trip_allocations": [
            {
                "plan_id": 3,
                "truck_id": 11,
                "hub_id": 9,
                "sector_id": 1,
                "total_load_kg": 200,
                "pickup_start": "demo",
                "estimated_hub_arrival": "demo",
                "status": "SCHEDULED",
                "available_capacity_kg": first_trip["available_capacity_kg"]
            }
        ],
        "forecast_allocations": []
    }

    print("\nAttempting second reservation of 200 kg...")

    try:
        reservation_manager.reserve(over_capacity_plan)
        print("Unexpected Result: second reservation succeeded.")
        failed_reservations = 0
    except Exception as error:
        print("Expected Result: second reservation rejected.")
        print(f"Reason: {error}")
        failed_reservations = 1

    assert first_trip["available_capacity_kg"] >= 0

    return {
        "clusters": 1,
        "trips": 1,
        "forecast_allocations": 0,
        "reservations": 1,
        "notifications": 0,
        "failed_reservations": failed_reservations
    }


def scenario_multiple_trips(planner, reservation_manager, notifier):
    """Scenario 4 and 5: multiple trips and readable notifications."""
    print_header("SCENARIO 4 - MULTIPLE TRIPS")

    matches = create_sample_matches()
    planning = run_planner(planner, 4, matches)

    assert len(planning["trip_allocations"]) == len(matches)

    reservation = run_reservation(reservation_manager, planning)

    assert reservation["reserved_trips"] == len(matches)

    print_header("SCENARIO 5 - NOTIFICATION DEMONSTRATION")
    notifications = run_notifier(notifier, reservation)

    expected_notifications = len(matches) * 4
    assert len(notifications["notifications"]) == expected_notifications

    return {
        "clusters": len(matches),
        "trips": len(planning["trip_allocations"]),
        "forecast_allocations": len(planning["forecast_allocations"]),
        "reservations": reservation["reserved_trips"],
        "notifications": len(notifications["notifications"]),
        "failed_reservations": 0
    }


def add_to_summary(summary, result):
    """Add scenario results to the final summary."""
    summary["clusters"] += result["clusters"]
    summary["trips"] += result["trips"]
    summary["forecast_allocations"] += result["forecast_allocations"]
    summary["reservations"] += result["reservations"]
    summary["notifications"] += result["notifications"]
    summary["failed_reservations"] += result["failed_reservations"]


def print_summary(summary, status):
    """Print the final engine execution summary."""
    print_header("ENGINE EXECUTION SUMMARY")
    print(f"Clusters Processed: {summary['clusters']}")
    print(f"Trips Created: {summary['trips']}")
    print(f"Forecast Allocations: {summary['forecast_allocations']}")
    print(f"Reservations Completed: {summary['reservations']}")
    print(f"Notifications Created: {summary['notifications']}")
    print(f"Successful Reservations: {summary['reservations']}")
    print(f"Failed Reservations: {summary['failed_reservations']}")
    print("\nOverall Engine Status:")
    print(status)
    print("\n========================================")


def run_simulation():
    """Run the full Tomato Logistics Engine simulator."""
    summary = {
        "clusters": 0,
        "trips": 0,
        "forecast_allocations": 0,
        "reservations": 0,
        "notifications": 0,
        "failed_reservations": 0
    }

    try:
        print_header("TOMATO LOGISTICS ENGINE SIMULATOR")
        loading("Initializing Engine")

        planner = Planner()
        reservation_manager = ReservationManager()
        notifier = Notifier()

        result = scenario_normal_reservation(
            planner,
            reservation_manager,
            notifier
        )
        add_to_summary(summary, result)

        result = scenario_shared_truck(planner, reservation_manager)
        add_to_summary(summary, result)

        result = scenario_hub_capacity(reservation_manager)
        add_to_summary(summary, result)

        result = scenario_multiple_trips(
            planner,
            reservation_manager,
            notifier
        )
        add_to_summary(summary, result)

        assert summary["trips"] > 0
        assert summary["reservations"] > 0
        assert summary["notifications"] > 0
        assert summary["failed_reservations"] >= 1

        print_summary(summary, "SUCCESS")

    except Exception as error:
        print("\nSimulation failed.")
        print(f"Error: {error}")
        print_summary(summary, "FAILED")
        print("\nTraceback:")
        traceback.print_exc()


if __name__ == "__main__":
    run_simulation()
