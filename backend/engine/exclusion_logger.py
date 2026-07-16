"""
Exclusion logging for the Tomato Logistics engine.

This module records forecasts or clusters that cannot continue through the
engine. It does not write to PostgreSQL. Instead, it creates plain dictionaries
that a future service layer can persist into an excluded_trips-style table.
"""

from datetime import datetime


class ExclusionLogger:
    """
    Collects structured exclusion records for rejected forecasts.

    The logger receives forecasts, clusters, or demand records and stores clear
    reasons for rejection. It returns dictionaries so the rest of the engine can
    continue processing valid data.
    """

    def __init__(self):
        """
        Create an empty exclusion logger.

        Receives no input. Returns an object with an internal list of exclusion
        records for the current engine run.
        """
        self.records = []

    def log_forecast(self, forecast, reason, description, stage):
        """
        Record one excluded forecast.

        Receives a forecast dictionary, reason code, description, and engine
        stage. Returns the structured exclusion record that was stored.
        """
        record = self.build_record(
            forecast=forecast,
            reason=reason,
            description=description,
            stage=stage,
        )
        self.records.append(record)
        return record

    def log_cluster(self, cluster, reason, description, stage):
        """
        Record every forecast inside an excluded cluster.

        Receives a cluster dictionary, reason code, description, and stage.
        Returns a list of exclusion records, one for each forecast in the
        cluster. If the cluster has no forecasts, one cluster-level record is
        created.
        """
        forecasts = cluster.get("forecasts", [])

        if not forecasts:
            record = self.build_record(
                forecast={
                    "sector_id": cluster.get("sector_id"),
                    "cluster_id": cluster.get("cluster_id"),
                },
                reason=reason,
                description=description,
                stage=stage,
            )
            self.records.append(record)
            return [record]

        records = []
        for forecast in forecasts:
            record = self.log_forecast(
                forecast,
                reason,
                description,
                stage,
            )
            records.append(record)
        return records

    def build_record(self, forecast, reason, description, stage):
        """
        Build a structured exclusion dictionary.

        Receives forecast-like data and reason details. Returns a dictionary
        ready for future database persistence.
        """
        return {
            "forecast_id": forecast.get("forecast_id"),
            "farmer_id": forecast.get("farmer_id"),
            "sector_id": forecast.get("sector_id"),
            "cluster_id": forecast.get("cluster_id"),
            "reason": reason,
            "reason_code": reason,
            "description": description,
            "reason_detail": description,
            "stage": stage,
            "timestamp": datetime.now(),
            "temporary_engine_state": True,
            "persistence_status": "PENDING_DATABASE_INSERT",
        }

    def get_records(self):
        """
        Return all exclusions collected so far.

        Receives no input. Returns a copy of the internal exclusion list.
        """
        return list(self.records)

    def clear(self):
        """
        Remove all stored exclusion records.

        Receives no input. Returns None after clearing the current run's data.
        """
        self.records.clear()
