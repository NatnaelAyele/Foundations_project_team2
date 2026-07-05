
-- farmers 
CREATE INDEX IF NOT EXISTS idx_farmers_user_id    ON farmers (user_id);
CREATE INDEX IF NOT EXISTS idx_farmers_sector_id  ON farmers (sector_id);
CREATE INDEX IF NOT EXISTS idx_farmers_phone      ON farmers (phone);         

-- transporters
CREATE INDEX IF NOT EXISTS idx_transporters_user_id   ON transporters (user_id);
CREATE INDEX IF NOT EXISTS idx_transporters_sector_id ON transporters (sector_id);

-- cold_hubs
CREATE INDEX IF NOT EXISTS idx_hubs_sector_id ON cold_hubs (sector_id);
CREATE INDEX IF NOT EXISTS idx_hubs_status    ON cold_hubs (operating_status); 

-- trucks
CREATE INDEX IF NOT EXISTS idx_trucks_transporter_id ON trucks (transporter_id);
CREATE INDEX IF NOT EXISTS idx_trucks_sector_status  ON trucks (sector_id, status); 
                                                                                    
CREATE INDEX IF NOT EXISTS idx_trucks_status         ON trucks (status);

-- harvest_forecasts
CREATE INDEX IF NOT EXISTS idx_forecasts_farmer_id    ON harvest_forecasts (farmer_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_status_date  ON harvest_forecasts (status, harvest_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_harvest_date ON harvest_forecasts (harvest_date);

-- coordination_plans
CREATE INDEX IF NOT EXISTS idx_plans_sector_id ON coordination_plans (sector_id);
CREATE INDEX IF NOT EXISTS idx_plans_status    ON coordination_plans (status);

-- trip_allocations
CREATE INDEX IF NOT EXISTS idx_alloc_plan_id      ON trip_allocations (plan_id);
CREATE INDEX IF NOT EXISTS idx_alloc_truck_id     ON trip_allocations (truck_id);
CREATE INDEX IF NOT EXISTS idx_alloc_hub_id       ON trip_allocations (hub_id);
CREATE INDEX IF NOT EXISTS idx_alloc_sector_id    ON trip_allocations (sector_id);
CREATE INDEX IF NOT EXISTS idx_alloc_status       ON trip_allocations (status);
CREATE INDEX IF NOT EXISTS idx_alloc_pickup_start ON trip_allocations (pickup_start); 

-- excluded_trips
CREATE INDEX IF NOT EXISTS idx_excl_forecast_id ON excluded_trips (forecast_id);
CREATE INDEX IF NOT EXISTS idx_excl_plan_id     ON excluded_trips (plan_id);
CREATE INDEX IF NOT EXISTS idx_excl_reason      ON excluded_trips (reason_code);   

-- notifications
CREATE INDEX IF NOT EXISTS idx_notif_trip_id ON notifications (related_trip_id);
CREATE INDEX IF NOT EXISTS idx_notif_phone   ON notifications (recipient_phone);

-- Partial index: the retry worker only ever scans QUEUED rows,
-- so index just those instead of the whole table (Postgres-only trick).
CREATE INDEX IF NOT EXISTS idx_notif_queued
    ON notifications (notification_id)
    WHERE status = 'QUEUED';