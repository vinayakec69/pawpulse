-- ==========================================================
-- PawPulse Shelter Care & Behavioral Monitoring Schema
-- Run this in your Supabase SQL Editor
-- ==========================================================

-- 1. Enclosures (Shelter Pens / Wards)
CREATE TABLE IF NOT EXISTS enclosures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    name TEXT NOT NULL,                         -- e.g. "Pen 2 - North Ward"
    description TEXT,
    cctv_source TEXT,                           -- e.g. "cctv_pen2.mp4"
    dimensions_meters JSONB DEFAULT '{"width": 8.0, "length": 12.0}'::jsonb
);

-- 2. Monitoring Zones (Food bowl, corner, bedding inside each enclosure)
CREATE TABLE IF NOT EXISTS zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    enclosure_id UUID REFERENCES enclosures(id) ON DELETE CASCADE,
    name TEXT NOT NULL,                         -- "Food Bowl", "Secluded Dark Corner"
    zone_type TEXT NOT NULL,                    -- "feeding", "isolation", "resting"
    color_hex TEXT DEFAULT '#9B5B87',
    polygon_normalized JSONB NOT NULL           -- Array of [x, y] coordinates (0.0 to 1.0)
);

-- 3. Animals (Residents)
CREATE TABLE IF NOT EXISTS animals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    track_id INTEGER UNIQUE NOT NULL,           -- ByteTrack persistent ID (e.g. 1, 2, 3)
    name TEXT NOT NULL,                         -- e.g. "Shanti", "Buddy", "Mochi"
    species TEXT NOT NULL,                      -- "dog" or "cat"
    breed TEXT,
    avatar_url TEXT,
    enclosure_id UUID REFERENCES enclosures(id) ON DELETE SET NULL,
    baseline_distance_m FLOAT DEFAULT 800.0,    -- Normal 24h distance expected
    baseline_rest_hours FLOAT DEFAULT 6.0,
    current_status TEXT DEFAULT 'Healthy',      -- "Healthy", "Resting", "Lethargic"
    is_flagged BOOLEAN DEFAULT FALSE
);

-- 4. Telemetry Logs (Movement & Activity stream)
CREATE TABLE IF NOT EXISTS telemetry_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    animal_id UUID REFERENCES animals(id) ON DELETE CASCADE,
    enclosure_id UUID REFERENCES enclosures(id) ON DELETE CASCADE,
    track_id INTEGER NOT NULL,
    video_timestamp_sec FLOAT NOT NULL,
    centroid_x FLOAT NOT NULL,
    centroid_y FLOAT NOT NULL,
    distance_step_m FLOAT DEFAULT 0.0,
    cumulative_distance_m FLOAT DEFAULT 0.0,
    speed_mps FLOAT DEFAULT 0.0,
    current_zone TEXT,                          -- "Food Bowl", "Secluded Corner", or null
    is_resting BOOLEAN DEFAULT FALSE
);

-- 5. Alerts (Caretaker Interventions)
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    animal_id UUID REFERENCES animals(id) ON DELETE CASCADE,
    enclosure_id UUID REFERENCES enclosures(id) ON DELETE CASCADE,
    severity TEXT NOT NULL,                     -- "CRITICAL", "WARNING", "INFO"
    alert_type TEXT NOT NULL,                   -- "LETHARGY", "ISOLATION", "MISSED_FEEDING"
    message TEXT NOT NULL,
    activity_ratio FLOAT,                       -- Current distance / Baseline distance
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by TEXT,
    resolved_at TIMESTAMPTZ
);

-- Enable Supabase Realtime on Alerts and Telemetry
ALTER PUBLICATION supabase_realtime ADD TABLE alerts;
ALTER PUBLICATION supabase_realtime ADD TABLE telemetry_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE animals;

-- Enable Public Read/Write for easy prototype setup (adjust with Auth later if needed)
ALTER TABLE enclosures ENABLE ROW LEVEL SECURITY;
ALTER TABLE zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE animals ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read enclosures" ON enclosures FOR SELECT USING (true);
CREATE POLICY "Allow public write enclosures" ON enclosures FOR ALL USING (true);

CREATE POLICY "Allow public read zones" ON zones FOR SELECT USING (true);
CREATE POLICY "Allow public write zones" ON zones FOR ALL USING (true);

CREATE POLICY "Allow public read animals" ON animals FOR SELECT USING (true);
CREATE POLICY "Allow public write animals" ON animals FOR ALL USING (true);

CREATE POLICY "Allow public read telemetry" ON telemetry_logs FOR SELECT USING (true);
CREATE POLICY "Allow public write telemetry" ON telemetry_logs FOR ALL USING (true);

CREATE POLICY "Allow public read alerts" ON alerts FOR SELECT USING (true);
CREATE POLICY "Allow public write alerts" ON alerts FOR ALL USING (true);

-- ==========================================================
-- Initial Sample Seed Data (Pen 2 + Shanti & Buddy)
-- ==========================================================
DO $$
DECLARE
    pen2_id UUID;
    shanti_id UUID;
    buddy_id UUID;
    mochi_id UUID;
BEGIN
    -- 1. Insert Pen 2
    INSERT INTO enclosures (name, description, cctv_source)
    VALUES ('Pen 2 - North Enclosure', 'Main rehabilitation ward with indoor/outdoor run', 'pen2_cctv.mp4')
    RETURNING id INTO pen2_id;

    -- 2. Insert Zones for Pen 2
    INSERT INTO zones (enclosure_id, name, zone_type, color_hex, polygon_normalized)
    VALUES 
        (pen2_id, 'Food & Water Bowl', 'feeding', '#52A684', '[[0.05, 0.70], [0.25, 0.70], [0.25, 0.95], [0.05, 0.95]]'::jsonb),
        (pen2_id, 'Secluded Dark Corner', 'isolation', '#E56B6F', '[[0.75, 0.05], [0.98, 0.05], [0.98, 0.35], [0.75, 0.35]]'::jsonb);

    -- 3. Insert Resident Animals
    INSERT INTO animals (track_id, name, species, breed, enclosure_id, baseline_distance_m, current_status, is_flagged)
    VALUES 
        (1, 'Buddy', 'dog', 'Golden Mix', pen2_id, 850.0, 'Healthy', FALSE)
    RETURNING id INTO buddy_id;

    INSERT INTO animals (track_id, name, species, breed, enclosure_id, baseline_distance_m, current_status, is_flagged)
    VALUES 
        (3, 'Shanti', 'dog', 'Indie Hound', pen2_id, 750.0, 'Lethargic', TRUE)
    RETURNING id INTO shanti_id;

    INSERT INTO animals (track_id, name, species, breed, enclosure_id, baseline_distance_m, current_status, is_flagged)
    VALUES 
        (2, 'Mochi', 'cat', 'Calico Domestic', pen2_id, 350.0, 'Resting', FALSE)
    RETURNING id INTO mochi_id;

    -- 4. Initial Alert for Shanti
    INSERT INTO alerts (animal_id, enclosure_id, severity, alert_type, message, activity_ratio)
    VALUES (
        shanti_id, 
        pen2_id, 
        'CRITICAL', 
        'LETHARGY', 
        '🚨 ALERT: Dog #3 (Shanti) has only moved 40m in the last 24h (5% of baseline) and stayed in the back corner. Possible early sign of illness/lethargy. Please check enclosure Pen 2!', 
        0.053
    );
END $$;
