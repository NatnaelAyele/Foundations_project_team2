-- ============================================================
-- FreshLink — USSD compatibility migration
--
-- Run AFTER the team's schema.sql:
--     psql -U postgres -d freshlink -f schema.sql
--     psql -U postgres -d freshlink -f migration_ussd_compat.sql
--
-- The team's schema stays the source of truth. This only ADDS what the
-- USSD, SMS and payment code needs. It changes nothing the engine or the
-- dashboards already rely on.
-- ============================================================

-- ------------------------------------------------------------
-- FARMERS
-- ------------------------------------------------------------

-- USSD greets the farmer by code: "Welcome 001"
ALTER TABLE farmers ADD COLUMN IF NOT EXISTS farmer_code VARCHAR(20);

-- The farmer chooses English or Kinyarwanda; we remember it.
ALTER TABLE farmers ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(5) NOT NULL DEFAULT 'en';

-- USSD access check: unregistered / disabled numbers cannot open the menu.
ALTER TABLE farmers ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Phone is the USSD login key, so it must be unique.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_farmers_phone'
    ) THEN
        ALTER TABLE farmers ADD CONSTRAINT uq_farmers_phone UNIQUE (phone);
    END IF;
END $$;

-- A USSD farmer has no browser login, so user_id must be optional.
ALTER TABLE farmers ALTER COLUMN user_id DROP NOT NULL;

-- Backfill codes for any farmers that already exist.
UPDATE farmers
SET farmer_code = LPAD(farmer_id::TEXT, 3, '0')
WHERE farmer_code IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_farmers_code'
    ) THEN
        ALTER TABLE farmers ADD CONSTRAINT uq_farmers_code UNIQUE (farmer_code);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_farmers_phone ON farmers (phone);


-- ------------------------------------------------------------
-- HARVEST FORECASTS
-- ------------------------------------------------------------

-- The farmer enters the harvest TIME on its own USSD screen (08:00).
ALTER TABLE harvest_forecasts ADD COLUMN IF NOT EXISTS harvest_time TIME NOT NULL DEFAULT '08:00';

-- The code reads updated_at after an update.
ALTER TABLE harvest_forecasts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- PostgreSQL has no ON UPDATE CURRENT_TIMESTAMP.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_forecast_updated_at ON harvest_forecasts;
CREATE TRIGGER trg_forecast_updated_at
    BEFORE UPDATE ON harvest_forecasts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- The status CHECK only allowed PENDING/ALLOCATED/CANCELLED in upper case.
-- The USSD code writes lower case, the engine needs 'excluded', and the
-- 3-day harvest window needs 'expired'. Accept both cases and all states.
ALTER TABLE harvest_forecasts DROP CONSTRAINT IF EXISTS chk_harvest_forecasts_status;
ALTER TABLE harvest_forecasts ADD CONSTRAINT chk_harvest_forecasts_status
    CHECK (LOWER(status) IN ('pending','allocated','cancelled','excluded','expired'));

ALTER TABLE harvest_forecasts ALTER COLUMN status SET DEFAULT 'pending';

CREATE INDEX IF NOT EXISTS idx_forecast_farmer_status
    ON harvest_forecasts (farmer_id, status, submitted_at);


-- ------------------------------------------------------------
-- NOTIFICATIONS  (the farmer SMS inbox)
-- ------------------------------------------------------------

-- The inbox is queried per farmer, and USSD menu 5 shows the last 3.
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS farmer_id INT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_notifications_farmer'
    ) THEN
        ALTER TABLE notifications ADD CONSTRAINT fk_notifications_farmer
            FOREIGN KEY (farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE;
    END IF;
END $$;

-- e.g. HARVEST_RECORDED / HARVEST_UPDATED / HARVEST_CANCELLED
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS notification_type VARCHAR(40) NOT NULL DEFAULT 'GENERAL';

-- SMS templates exist in English and Kinyarwanda.
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS language VARCHAR(5) NOT NULL DEFAULT 'en';

-- The inbox sorts by sent_time DESC. NULLs would sort first and break it.
ALTER TABLE notifications ALTER COLUMN sent_time SET DEFAULT CURRENT_TIMESTAMP;
UPDATE notifications SET sent_time = CURRENT_TIMESTAMP WHERE sent_time IS NULL;

-- recipient_type is NOT NULL in the team schema but the USSD code does not
-- send it, so give it a default.
ALTER TABLE notifications ALTER COLUMN recipient_type SET DEFAULT 'FARMER';

-- Status: code writes pending / sent / failed.
ALTER TABLE notifications ALTER COLUMN status SET DEFAULT 'pending';
ALTER TABLE notifications ALTER COLUMN status TYPE VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_notifications_farmer_time
    ON notifications (farmer_id, sent_time DESC);


-- ------------------------------------------------------------
-- PAYMENTS
-- ------------------------------------------------------------

-- Our own unique reference sent to Flutterwave. The webhook only knows
-- this value, so it is how we find the payment again.
ALTER TABLE payments ADD COLUMN IF NOT EXISTS tx_ref VARCHAR(100);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_payments_tx_ref'
    ) THEN
        ALTER TABLE payments ADD CONSTRAINT uq_payments_tx_ref UNIQUE (tx_ref);
    END IF;
END $$;

-- Last provider response or error message.
ALTER TABLE payments ADD COLUMN IF NOT EXISTS provider_message TEXT;

-- Allow charges before the coordination engine exists, and when the payee
-- phone is not yet known.
ALTER TABLE payments ALTER COLUMN allocation_id DROP NOT NULL;
ALTER TABLE payments ALTER COLUMN payee_phone DROP NOT NULL;

ALTER TABLE payments ALTER COLUMN status SET DEFAULT 'pending';

CREATE INDEX IF NOT EXISTS idx_payments_tx_ref ON payments (tx_ref);
CREATE INDEX IF NOT EXISTS idx_payments_farmer ON payments (farmer_id, created_at);


-- ------------------------------------------------------------
-- Done
-- ------------------------------------------------------------
SELECT 'USSD compatibility migration applied' AS result;
