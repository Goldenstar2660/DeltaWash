# Data Model: Hospital Dashboard

**Feature**: Hospital Dashboard for Handwashing Compliance Analytics  
**Created**: January 10, 2026  
**Purpose**: Define entities, relationships, schemas, and database structure

## Entity Definitions

### Device

Represents a physical handwashing compliance system deployed at a hospital unit.

**Attributes**:
- `id` (UUID, primary key): Unique identifier for the device
- `unit_id` (UUID, foreign key → Unit): Unit where device is installed
- `device_name` (string, max 100 chars): Human-readable name (e.g., "ICU-Device-01")
- `firmware_version` (string, max 20 chars): Current firmware version reported by device (e.g., "v1.2.3")
- `installation_date` (timestamp): Date device was first installed
- `created_at` (timestamp): Record creation timestamp
- `updated_at` (timestamp): Record last update timestamp

**Relationships**:
- One Device belongs to one Unit (many-to-one)
- One Device has many Sessions (one-to-many)
- One Device has many Heartbeats (one-to-many)

**Validation Rules**:
- `device_name` must be unique within a unit
- `firmware_version` must match semantic versioning pattern (e.g., vX.Y.Z)
- `installation_date` cannot be in the future

**State Transitions**: None (static reference data)

---

### Unit

Represents a physical location or organizational division within a hospital (e.g., ICU, ER, Surgery).

**Attributes**:
- `id` (UUID, primary key): Unique identifier for the unit
- `unit_name` (string, max 100 chars): Human-readable name (e.g., "Intensive Care Unit")
- `unit_code` (string, max 20 chars): Short code for displays (e.g., "ICU")
- `hospital_id` (UUID, optional): Identifier for parent hospital (null for single-hospital MVP)
- `created_at` (timestamp): Record creation timestamp

**Relationships**:
- One Unit has many Devices (one-to-many)
- One Unit has many Sessions (via Devices, one-to-many)

**Validation Rules**:
- `unit_code` must be unique across all units
- `unit_name` must be unique within a hospital (if `hospital_id` is set)

**State Transitions**: None (static reference data)

---

### Session

Represents a single handwashing event performed at a device.

**Attributes**:
- `id` (UUID, primary key): Unique identifier for the session
- `device_id` (UUID, foreign key → Device): Device that recorded the session
- `timestamp` (timestamp with time zone): Session start time (UTC)
- `duration_ms` (integer): Total session duration in milliseconds
- `compliant` (boolean): Whether session met all WHO step requirements
- `low_quality` (boolean): Whether session was flagged as low-quality due to poor hand detection or coverage
- `missed_steps` (integer array): Array of step IDs that were not completed (e.g., `[3, 5]` means steps 3 and 5 were missed)
- `config_version` (string, max 50 chars): Config hash from device at time of session
- `created_at` (timestamp): Record creation timestamp

**Relationships**:
- One Session belongs to one Device (many-to-one)
- One Session has many Steps (one-to-many)

**Validation Rules**:
- `duration_ms` must be between 5,000 (5s) and 120,000 (2 minutes)
- `compliant = True` only if `missed_steps` is empty AND all steps have `completed = True`
- `timestamp` cannot be in the future
- `missed_steps` must contain valid step IDs (2-7 only)

**State Transitions**: None (immutable after ingestion)

**Derived Fields** (not stored, computed in queries):
- `compliance_rate` (for aggregates): `COUNT(*) FILTER (WHERE compliant = TRUE) / COUNT(*)`
- `average_duration` (for aggregates): `AVG(duration_ms)`

---

### Step

Represents a specific WHO handwashing step within a session.

**Attributes**:
- `id` (UUID, primary key): Unique identifier for the step record
- `session_id` (UUID, foreign key → Session): Parent session
- `step_id` (integer): WHO step identifier (2-7)
- `duration_ms` (integer): Time spent on this step in milliseconds
- `completed` (boolean): Whether step met minimum duration and quality thresholds
- `confidence_score` (float, 0.0-1.0, optional): Detection confidence from ML model (if available)
- `created_at` (timestamp): Record creation timestamp

**Relationships**:
- One Step belongs to one Session (many-to-one)

**Validation Rules**:
- `step_id` must be in range [2, 7] (WHO steps 2-7 only)
- `duration_ms` must be non-negative
- `completed = True` only if `duration_ms` >= minimum threshold for step (varies by step; e.g., step 2 requires 5s)
- `confidence_score` must be between 0.0 and 1.0 if present

**State Transitions**: None (immutable after ingestion)

**Step ID Reference** (from WHO hand-rubbing technique):
- Step 2: Palm to palm
- Step 3: Right palm over left dorsum / Left palm over right dorsum
- Step 4: Palm to palm with fingers interlaced
- Step 5: Backs of fingers to opposing palms
- Step 6: Rotational rubbing of thumbs
- Step 7: Rotational rubbing of fingertips

---

### Heartbeat

Represents a device health check event sent periodically by devices.

**Attributes**:
- `id` (UUID, primary key): Unique identifier for the heartbeat
- `device_id` (UUID, foreign key → Device): Device that sent the heartbeat
- `timestamp` (timestamp with time zone): Heartbeat timestamp (UTC)
- `firmware_version` (string, max 20 chars): Firmware version at time of heartbeat
- `online_status` (boolean): Whether device reported online (true) or offline (false)
- `created_at` (timestamp): Record creation timestamp

**Relationships**:
- One Heartbeat belongs to one Device (many-to-one)

**Validation Rules**:
- `timestamp` cannot be in the future
- `firmware_version` must match semantic versioning pattern

**State Transitions**: None (immutable after ingestion)

**Derived Fields** (not stored, computed in queries):
- `last_seen` (per device): `MAX(timestamp) WHERE device_id = X`
- `is_offline` (per device): `last_seen < NOW() - INTERVAL '1 hour'`
- `heartbeats_24h` (per device): `COUNT(*) WHERE timestamp > NOW() - INTERVAL '24 hours'`

---

### User

Represents a dashboard user with role-based access control.

**Attributes**:
- `id` (UUID, primary key): Unique identifier for the user
- `email` (string, max 255 chars): User email address (used for login)
- `password_hash` (string, max 255 chars): Bcrypt-hashed password
- `role` (enum): User role (org_admin, analyst, unit_manager, technician)
- `unit_id` (UUID, foreign key → Unit, nullable): Assigned unit for unit_manager role (null for other roles)
- `created_at` (timestamp): Record creation timestamp
- `last_login_at` (timestamp, nullable): Last successful login timestamp

**Relationships**:
- One User optionally belongs to one Unit (many-to-one, nullable)

**Validation Rules**:
- `email` must be unique and match email regex pattern
- `password_hash` must be bcrypt hash (starts with `$2b$`)
- `role` must be one of: `org_admin`, `analyst`, `unit_manager`, `technician`
- `unit_id` must be non-null if `role = unit_manager`; must be null for other roles

**State Transitions**: 
- `last_login_at` updated on successful authentication

**Security Notes**:
- Never expose `password_hash` in API responses
- Password must be minimum 8 characters before hashing

---

## Entity Relationships Diagram

```text
┌─────────────┐
│   Hospital  │ (future: multi-hospital support)
│   (optional)│
└──────┬──────┘
       │
       │ 1:N
       ▼
┌─────────────┐       1:N       ┌─────────────┐       1:N       ┌─────────────┐
│    Unit     │◄────────────────┤   Device    │◄────────────────┤   Session   │
│             │                 │             │                 │             │
└─────────────┘                 └──────┬──────┘                 └──────┬──────┘
       ▲                               │                               │
       │                               │ 1:N                           │ 1:N
       │                               ▼                               ▼
       │                        ┌─────────────┐                 ┌─────────────┐
       │                        │  Heartbeat  │                 │    Step     │
       │                        │             │                 │             │
       │                        └─────────────┘                 └─────────────┘
       │
       │ 0:N (nullable)
       │
┌─────────────┐
│    User     │
│  (RBAC)     │
└─────────────┘
```

**Relationship Descriptions**:
- Hospital → Unit: One hospital has many units (future multi-hospital support)
- Unit → Device: One unit has many devices (current scope)
- Device → Session: One device records many sessions (one session per handwash event)
- Device → Heartbeat: One device sends many heartbeats (periodic health checks)
- Session → Step: One session contains many steps (one record per WHO step attempted)
- Unit → User: One unit has many unit_manager users (optional for unit_manager role)

---

## Database Schema

### Tables

```sql
-- Units table
CREATE TABLE units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_name VARCHAR(100) NOT NULL,
    unit_code VARCHAR(20) NOT NULL UNIQUE,
    hospital_id UUID,  -- Future: foreign key to hospitals table
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_units_hospital_id ON units(hospital_id);

-- Devices table
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id UUID NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    device_name VARCHAR(100) NOT NULL,
    firmware_version VARCHAR(20),
    installation_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(unit_id, device_name)
);

CREATE INDEX idx_devices_unit_id ON devices(unit_id);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_ms INTEGER NOT NULL CHECK (duration_ms >= 5000 AND duration_ms <= 120000),
    compliant BOOLEAN NOT NULL,
    low_quality BOOLEAN NOT NULL DEFAULT FALSE,
    missed_steps INTEGER[] DEFAULT '{}',
    config_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sessions_device_timestamp ON sessions(device_id, timestamp DESC);
CREATE INDEX idx_sessions_timestamp ON sessions(timestamp DESC);
CREATE INDEX idx_sessions_compliant ON sessions(compliant);
CREATE INDEX idx_sessions_low_quality ON sessions(low_quality);

-- Steps table
CREATE TABLE steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    step_id INTEGER NOT NULL CHECK (step_id >= 2 AND step_id <= 7),
    duration_ms INTEGER NOT NULL CHECK (duration_ms >= 0),
    completed BOOLEAN NOT NULL,
    confidence_score REAL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_steps_session_id ON steps(session_id);
CREATE INDEX idx_steps_step_id ON steps(step_id);

-- Heartbeats table
CREATE TABLE heartbeats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    firmware_version VARCHAR(20),
    online_status BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_heartbeats_device_timestamp ON heartbeats(device_id, timestamp DESC);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('org_admin', 'analyst', 'unit_manager', 'technician')),
    unit_id UUID REFERENCES units(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    CHECK (
        (role = 'unit_manager' AND unit_id IS NOT NULL) OR
        (role != 'unit_manager' AND unit_id IS NULL)
    )
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### Materialized Views

```sql
-- Daily compliance rate per device/unit
CREATE MATERIALIZED VIEW mv_daily_compliance AS
SELECT
    DATE(s.timestamp) AS date,
    s.device_id,
    d.unit_id,
    COUNT(*) AS total_sessions,
    COUNT(*) FILTER (WHERE s.compliant = TRUE) AS compliant_sessions,
    ROUND(100.0 * COUNT(*) FILTER (WHERE s.compliant = TRUE) / COUNT(*), 2) AS compliance_rate,
    ROUND(AVG(s.duration_ms), 2) AS avg_duration_ms
FROM sessions s
JOIN devices d ON s.device_id = d.id
WHERE s.low_quality = FALSE  -- Exclude low-quality sessions from compliance metrics
GROUP BY DATE(s.timestamp), s.device_id, d.unit_id;

CREATE UNIQUE INDEX idx_mv_daily_compliance ON mv_daily_compliance(date, device_id);
CREATE INDEX idx_mv_daily_compliance_unit ON mv_daily_compliance(unit_id, date);

-- Step-level statistics (most missed steps, average durations)
CREATE MATERIALIZED VIEW mv_step_statistics AS
SELECT
    st.step_id,
    COUNT(*) AS total_attempts,
    COUNT(*) FILTER (WHERE st.completed = FALSE) AS missed_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE st.completed = FALSE) / COUNT(*), 2) AS miss_rate,
    ROUND(AVG(st.duration_ms), 2) AS avg_duration_ms
FROM steps st
JOIN sessions s ON st.session_id = s.id
WHERE s.low_quality = FALSE  -- Exclude low-quality sessions
GROUP BY st.step_id;

CREATE UNIQUE INDEX idx_mv_step_statistics ON mv_step_statistics(step_id);

-- Device status summary
CREATE MATERIALIZED VIEW mv_device_status AS
SELECT
    d.id AS device_id,
    d.unit_id,
    d.device_name,
    d.firmware_version,
    MAX(h.timestamp) AS last_seen,
    COUNT(h.id) FILTER (WHERE h.timestamp > NOW() - INTERVAL '24 hours') AS heartbeats_24h,
    CASE WHEN MAX(h.timestamp) < NOW() - INTERVAL '1 hour' THEN TRUE ELSE FALSE END AS is_offline
FROM devices d
LEFT JOIN heartbeats h ON d.id = h.device_id
GROUP BY d.id, d.unit_id, d.device_name, d.firmware_version;

CREATE UNIQUE INDEX idx_mv_device_status ON mv_device_status(device_id);
CREATE INDEX idx_mv_device_status_unit ON mv_device_status(unit_id);
```

---

## Data Flow

### 1. Live Device Ingestion

```text
┌─────────────┐                              ┌─────────────┐
│   Device    │  HTTP POST                   │   Backend   │
│ (Raspberry  │  /api/v1/events/session      │   (FastAPI) │
│    Pi)      ├─────────────────────────────►│             │
│             │  JSON: {device_id,           │             │
│             │   timestamp, duration_ms,    │             │
│             │   compliant, missed_steps}   │             │
└─────────────┘                              └──────┬──────┘
                                                    │
                                                    │ INSERT
                                                    ▼
                                             ┌─────────────┐
                                             │ PostgreSQL  │
                                             │   (sessions │
                                             │    table)   │
                                             └─────────────┘
```

**Flow Steps**:
1. Device completes session and generates session record
2. Device HTTP client POSTs JSON to `/api/v1/events/session`
3. Backend validates payload (Pydantic schema)
4. Backend INSERTs into `sessions` table
5. Backend returns 201 Created with session ID
6. If HTTP fails, device logs error but continues detection (fail-safe)

**Step/Heartbeat Ingestion**: Same pattern for `/api/v1/events/step` and `/api/v1/events/heartbeat`

---

### 2. Demo Data Generation

```text
┌─────────────┐                              ┌─────────────┐
│  Admin User │  CLI command                 │   Script    │
│ (Hackathon  │  seed_demo_data.py           │  (Python)   │
│ Presenter)  ├─────────────────────────────►│             │
│             │  --devices 20 --days 7       │ ┌─────────┐ │
│             │  --sessions-per-day 10       │ │ Faker + │ │
│             │  --seed 42                   │ │  NumPy  │ │
└─────────────┘                              │ └────┬────┘ │
                                             └──────┼──────┘
                                                    │
                                                    │ Bulk INSERT
                                                    ▼
                                             ┌─────────────┐
                                             │ PostgreSQL  │
                                             │  (units,    │
                                             │  devices,   │
                                             │  sessions,  │
                                             │  steps,     │
                                             │  heartbeats)│
                                             └─────────────┘
```

**Flow Steps**:
1. Admin runs `docker-compose run --rm backend python -m src.scripts.seed_demo_data --seed 42`
2. Script generates:
   - 3-5 units
   - 20 devices distributed across units
   - 7 days of sessions (~10 per device per day = ~1400 total sessions)
   - Steps for each session (6 steps × 1400 sessions = ~8400 step records)
   - Heartbeats every 5 minutes when device online (~20 devices × 7 days × 288/day = ~40,320 heartbeats)
3. Script uses bulk INSERT for performance (SQLAlchemy `bulk_insert_mappings`)
4. Script validates totals and logs summary

---

### 3. Dashboard Query

```text
┌─────────────┐                              ┌─────────────┐
│ Frontend    │  HTTP GET                    │   Backend   │
│  (React)    │  /api/v1/analytics/overview  │  (FastAPI)  │
│             │  ?date_from=2026-01-10       │             │
│             │  &date_to=2026-01-10         │             │
│             │  &unit_id=abc123             │             │
│             ├─────────────────────────────►│             │
│             │                              │             │
│             │◄─────────────────────────────┤             │
│             │  JSON: {compliance_trend,    └──────┬──────┘
│             │   most_missed_step,                 │
│             │   avg_wash_time, ...}               │ SELECT
│             │                                     ▼
└─────────────┘                              ┌─────────────┐
                                             │ PostgreSQL  │
                                             │   (mv_daily_│
                                             │  compliance,│
                                             │  mv_step_   │
                                             │ statistics) │
                                             └─────────────┘
```

**Flow Steps**:
1. Frontend fetches analytics data with React Query
2. Backend receives query params (filters: date range, unit, shift, quality toggle)
3. Backend queries materialized views with WHERE clauses for filters
4. Backend aggregates results (e.g., GROUP BY date for trend chart)
5. Backend returns JSON response (Pydantic schema serialization)
6. Frontend renders charts (Recharts components)

---

## Data Retention and Cleanup

**MVP Policy**: Unlimited retention (no automatic deletion)

**Future Considerations**:
- Partition `sessions` table by month after 6+ months of data
- Archive old sessions to cold storage (S3-compatible) after 1 year
- Implement `DELETE` endpoint with date range for manual cleanup

---

## Schema Evolution

**Migration Strategy**: Alembic for version-controlled migrations

**Initial Migration** (`001_initial_schema.py`):
- Create all tables
- Create indexes
- Create materialized views

**Future Migrations** (examples):
- Add `hospital_id` foreign key to `units` for multi-hospital support
- Add `shift` enum to `sessions` for pre-computed shift assignment
- Add `video_url` to `sessions` for optional video storage (Out of Scope for MVP)

**Best Practices**:
- Never drop columns (mark deprecated, add new column)
- Always add `IF NOT EXISTS` clauses for idempotent migrations
- Test migrations on copy of production data before deploying
