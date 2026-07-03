-------------------------------------------------------------
-- SEED DATA FOR TOMATO LOGISTICS PLATFORM
-------------------------------------------------------------

-- USERS

INSERT INTO users
    (username, password_hash, role)
VALUES
    ('admin', '$2b$dummyhash_admin', 'ADMIN'),
    ('farmer_john', '$2b$dummyhash1', 'FARMER'),
    ('farmer_mary', '$2b$dummyhash2', 'FARMER'),
    ('farmer_peter', '$2b$dummyhash3', 'FARMER'),
    ('transporter_alpha', '$2b$dummyhash4', 'TRANSPORTER'),
    ('transporter_beta', '$2b$dummyhash5', 'TRANSPORTER');

-- Sectors

INSERT INTO sectors
    (name, district, cell, village)
VALUES
    ('Kimironko', 'Gasabo', 'Bibare', 'Nyagatovu'),
    ('Remera', 'Gasabo', 'Rukiri II', 'Gisimenti'),
    ('Kacyiru', 'Gasabo', 'Kamatamu', 'Kamatamu');

-- Farmers

INSERT INTO farmers
    (user_id, sector_id, name, phone, cell, village)
VALUES
    (2, 1, 'John Mwangi', '0781234567', 'Bibare', 'Nyagatovu'),
    (3, 2, 'Mary Uwase', '0782345678', 'Rukiri II', 'Gisimenti'),
    (4, 3, 'Peter Niyonsenga', '0783456789', 'Kamatamu', 'Kamatamu');



INSERT INTO transporters
    (user_id, sector_id, name, phone)
VALUES
    (5, 1, 'Alpha Logistics', '0789001111'),
    (6, 2, 'Beta Transport', '0789002222');


INSERT INTO cold_hubs
    (
    sector_id,
    name,
    phone,
    total_capacity_kg,
    available_capacity_kg,
    operating_status
    )
VALUES
    (1, 'Kimironko Cold Hub', '0788001111', 5000, 5000, 'OPEN'),
    (2, 'Remera Cold Hub', '0788002222', 4000, 3500, 'OPEN'),
    (3, 'Kacyiru Cold Hub', '0788003333', 3000, 3000, 'OPEN');

-------------------------------------------------------------
-- TRUCKS
-------------------------------------------------------------

INSERT INTO trucks
    (
    transporter_id,
    plate_number,
    capacity_kg,
    sector_id,
    status
    )
VALUES
    (1, 'RAB123A', 2000, 1, 'IDLE'),
    (1, 'RAB124A', 1500, 1, 'IDLE'),
    (2, 'RAB225B', 3000, 2, 'IDLE');



INSERT INTO harvest_forecasts
    (
    farmer_id,
    quantity_kg,
    harvest_date,
    status
    )
VALUES
    (1, 800, '2026-07-10 08:00:00', 'PENDING'),
    (2, 1200, '2026-07-10 09:00:00', 'PENDING'),
    (3, 600, '2026-07-11 08:30:00', 'PENDING');


INSERT INTO coordination_plans
    (
    sector_id,
    status
    )
VALUES
    (1, 'GENERATED'),
    (2, 'GENERATED');


INSERT INTO trip_allocations
    (
    plan_id,
    truck_id,
    hub_id,
    sector_id,
    total_load_kg,
    pickup_start,
    estimated_hub_arrival,
    status
    )
VALUES
    (
        1,
        1,
        1,
        1,
        1800,
        '2026-07-10 07:30:00',
        '2026-07-10 09:00:00',
        'SCHEDULED'
),
    (
        2,
        3,
        2,
        2,
        1200,
        '2026-07-10 08:15:00',
        '2026-07-10 09:30:00',
        'SCHEDULED'
);



INSERT INTO excluded_trips
    (
    forecast_id,
    plan_id,
    reason_code
    )
VALUES
    (
        3,
        2,
        'INSUFFICIENT_CAPACITY'
);


INSERT INTO notifications
    (
    recipient_type,
    recipient_phone,
    channel,
    message,
    status,
    sent_time,
    related_trip_id
    )
VALUES
    (
        'FARMER',
        '0781234567',
        'SMS',
        'Your tomatoes will be collected at 07:30.',
        'SENT',
        CURRENT_TIMESTAMP,
        1
),
    (
        'TRANSPORTER',
        '0789001111',
        'SMS',
        'Truck RAB123A has been assigned.',
        'SENT',
        CURRENT_TIMESTAMP,
        1
),
    (
        'FARMER',
        '0782345678',
        'SMS',
        'Your harvest has been scheduled.',
        'SENT',
        CURRENT_TIMESTAMP,
        2
);