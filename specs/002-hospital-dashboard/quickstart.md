# Quickstart: Hospital Dashboard

**Feature**: Hospital Dashboard for Handwashing Compliance Analytics  
**Created**: January 10, 2026  
**Purpose**: Get dashboard running locally with demo data for DeltaHacks presentation

## Prerequisites

- Docker Desktop installed and running (MacOS/Linux/Windows)
- Git (to clone repository)
- 8GB RAM available for Docker containers
- Modern browser (Chrome, Firefox, Safari, Edge)

---

## Quick Start (5 Minutes)

### 1. Clone and Navigate

```bash
cd handwash
git checkout 002-hospital-dashboard
```

### 2. Start Dashboard Stack

```bash
# One-command startup
docker-compose -f docker-compose.dashboard.yml up --build
```

**What this does**:
- Builds backend (FastAPI) and frontend (React+Vite) images
- Starts PostgreSQL 16 database
- Initializes database schema and materialized views
- Seeds demo data (20 devices, 7 days, 1400+ sessions)
- Starts API server on `http://localhost:8000`
- Starts frontend on `http://localhost:5173`

**Wait for**:
```
backend_1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend_1  | VITE v5.0.0  ready in 1234 ms
frontend_1  | ➜  Local: http://localhost:5173/
```

### 3. Access Dashboard

**URL**: `http://localhost:5173`

**Default Login Credentials**:
- Email: `admin@demo.com`
- Password: `demo1234`
- Role: Org Admin (full access)

### 4. Explore Demo Data

**Overview Dashboard** (default landing page):
- Compliance trend chart (7 days)
- Most missed step indicator
- Average wash time: ~31 seconds
- Quality rate: ~88%
- Device status: 18/20 online

**Try Filters**:
1. Date range: Select "Last 3 days" → metrics recalculate
2. Unit filter: Select "ICU" → metrics scope to ICU devices only
3. Shift filter: Select "Morning (7am-3pm)" → metrics show morning sessions
4. Quality toggle: Enable "Exclude low-quality" → metrics exclude flagged sessions

**Unit Drilldown**:
- Click "View Units" → Select "ICU"
- See ICU-specific compliance trend
- Device leaderboard: Best to worst performers

**Device View**:
- Click any device from leaderboard
- Last seen timestamp
- Heartbeat metrics (288/day = every 5 minutes)
- Firmware version: v1.2.3
- Reliability flags (if any offline periods)

---

## Demo Reset (1 Command)

Wipe all data and regenerate fresh demo data:

```bash
# From repository root
./scripts/reset-demo.sh
```

**What this does**:
1. Stops all containers
2. Removes database volume (wipes data)
3. Restarts PostgreSQL
4. Recreates schema
5. Seeds new demo data (same seed = same data)
6. Restarts backend + frontend

**Duration**: ~30 seconds

---

## Manual Commands

### Generate Demo Data with Custom Parameters

```bash
# Run from repository root
docker-compose -f docker-compose.dashboard.yml run --rm backend \
  python -m src.scripts.seed_demo_data \
    --devices 25 \
    --days 14 \
    --sessions-per-day 15 \
    --miss-rate 0.20 \
    --low-quality-rate 0.15 \
    --offline-rate 0.10 \
    --seed 99
```

**Parameters**:
- `--devices`: Number of devices (default: 20)
- `--days`: Historical days (default: 7)
- `--sessions-per-day`: Average sessions per device per day (default: 10)
- `--miss-rate`: Probability of missing a step (default: 0.15 = 15%)
- `--low-quality-rate`: Probability of low-quality session (default: 0.12 = 12%)
- `--offline-rate`: Probability device offline per day (default: 0.08 = 8%)
- `--seed`: Random seed for reproducibility (default: 42)

### Refresh Materialized Views

After bulk data ingestion, refresh aggregates:

```bash
docker-compose -f docker-compose.dashboard.yml exec backend \
  python -m src.scripts.refresh_views
```

### Create Additional Users

```bash
# Org Admin
docker-compose -f docker-compose.dashboard.yml exec backend \
  python -m src.scripts.create_user \
    --email analyst@demo.com \
    --password demo1234 \
    --role analyst

# Unit Manager (requires unit_id)
docker-compose -f docker-compose.dashboard.yml exec backend \
  python -m src.scripts.create_user \
    --email icu-manager@demo.com \
    --password demo1234 \
    --role unit_manager \
    --unit-id <unit-uuid>
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.dashboard.yml logs -f

# Backend only
docker-compose -f docker-compose.dashboard.yml logs -f backend

# Frontend only
docker-compose -f docker-compose.dashboard.yml logs -f frontend
```

### Stop Services

```bash
# Stop but keep data
docker-compose -f docker-compose.dashboard.yml down

# Stop and remove volumes (wipes data)
docker-compose -f docker-compose.dashboard.yml down -v
```

---

## API Documentation

**Swagger UI**: `http://localhost:8000/docs`

**OpenAPI JSON**: `http://localhost:8000/openapi.json`

Explore all endpoints interactively. Use "Authorize" button to add JWT token after logging in.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Compose                        │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Frontend   │      │   Backend    │      │ PostgreSQL│ │
│  │  (React+Vite)│◄────►│  (FastAPI)   │◄────►│    16     │ │
│  │  Port: 5173  │      │  Port: 8000  │      │Port: 5432 │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         ▲
         │ Browser: http://localhost:5173
         │
   ┌─────────────┐
   │   Device    │  HTTP POST to http://localhost:8000/api/v1/events
   │(Raspberry Pi)│  (optional: connect real device after dashboard running)
   └─────────────┘
```

**Data Flow**:
1. Frontend makes API requests to `http://localhost:8000/api/v1/`
2. Backend queries PostgreSQL (direct SQLAlchemy + materialized views)
3. Backend returns JSON (Pydantic schemas)
4. Frontend renders charts (Recharts)

---

## Connecting a Real Device (Optional)

If you have a Raspberry Pi handwashing device:

### 1. Update Device Configuration

Edit `config/local.yaml` on Raspberry Pi:

```yaml
dashboard:
  enabled: true
  api_url: http://<your-laptop-ip>:8000/api/v1
  device_id: <device-uuid-from-dashboard>
  api_token: <device-jwt-token>
```

**Get laptop IP**:
- MacOS: `ifconfig | grep inet`
- Linux: `ip addr show`
- Windows: `ipconfig`

### 2. Create Device Token

```bash
docker-compose -f docker-compose.dashboard.yml exec backend \
  python -m src.scripts.create_device_token \
    --device-id <device-uuid>
```

Returns JWT token with `device` role for event ingestion.

### 3. Test Connection

Run handwashing session on device → session appears in dashboard within 5 seconds.

---

## Troubleshooting

### Dashboard Not Loading

**Symptom**: Browser shows "Connection refused" at `http://localhost:5173`

**Fix**:
```bash
# Check if containers are running
docker-compose -f docker-compose.dashboard.yml ps

# If not running, start them
docker-compose -f docker-compose.dashboard.yml up
```

### No Data in Dashboard

**Symptom**: Dashboard loads but shows "No data available"

**Fix**:
```bash
# Verify database has data
docker-compose -f docker-compose.dashboard.yml exec db \
  psql -U dashboard -d dashboard_db -c "SELECT COUNT(*) FROM sessions;"

# If count is 0, reseed data
./scripts/reset-demo.sh
```

### Slow Dashboard Queries

**Symptom**: Filters take >3 seconds to update

**Fix**:
```bash
# Refresh materialized views
docker-compose -f docker-compose.dashboard.yml exec backend \
  python -m src.scripts.refresh_views

# Check view refresh timestamps
docker-compose -f docker-compose.dashboard.yml exec db \
  psql -U dashboard -d dashboard_db -c \
    "SELECT schemaname, matviewname, last_refresh FROM pg_matviews;"
```

### Backend Startup Errors

**Symptom**: Backend container exits with database connection error

**Fix**:
```bash
# Check if database is ready
docker-compose -f docker-compose.dashboard.yml exec db pg_isready

# If not ready, wait 10 seconds and restart backend
docker-compose -f docker-compose.dashboard.yml restart backend
```

### Port Conflicts

**Symptom**: "Port 5173 is already in use" or "Port 8000 is already in use"

**Fix**:
```bash
# Kill process using port (MacOS/Linux)
lsof -ti:5173 | xargs kill
lsof -ti:8000 | xargs kill

# Or change ports in docker-compose.dashboard.yml
# frontend: ports: ["3000:5173"]
# backend: ports: ["9000:8000"]
```

---

## Development Workflow

### Hot Reload

**Frontend**: Code changes in `dashboard/frontend/src/` auto-reload in browser (Vite HMR)

**Backend**: Code changes in `dashboard/backend/src/` auto-reload server (Uvicorn `--reload`)

### Run Tests

```bash
# Backend integration tests
docker-compose -f docker-compose.dashboard.yml exec backend \
  pytest tests/integration/ -v

# Backend unit tests
docker-compose -f docker-compose.dashboard.yml exec backend \
  pytest tests/unit/ -v

# Frontend unit tests
docker-compose -f docker-compose.dashboard.yml exec frontend \
  npm run test

# Frontend smoke tests (requires dashboard running)
cd dashboard/frontend
npx playwright test
```

### Access Database Directly

```bash
# psql shell
docker-compose -f docker-compose.dashboard.yml exec db \
  psql -U dashboard -d dashboard_db

# Example queries
\dt                              # List tables
SELECT COUNT(*) FROM sessions;   # Count sessions
SELECT * FROM mv_daily_compliance LIMIT 5;  # View materialized view
```

---

## DeltaHacks Presentation Tips

### Demo Script

**Opening** (30 seconds):
- "We built a handwashing compliance dashboard for hospitals"
- "Problem: One physical device, but need to demo analytics for 20+ devices"
- "Solution: Synthetic data generation with realistic patterns"

**Demo Flow** (2 minutes):
1. Show overview dashboard: "Here's 20 devices across 4 hospital units over 7 days"
2. Apply filter: "Let's scope to ICU only" → metrics update instantly
3. Unit drilldown: "Here's the ICU device leaderboard—Device-01 has 95% compliance"
4. Device view: "Device-02 went offline for 4 hours on January 10th"
5. Reset: "Watch this—I'll wipe and reseed all data in 30 seconds" → run `./scripts/reset-demo.sh`

**Closing** (15 seconds):
- "Built with Python FastAPI, PostgreSQL, React TypeScript, all running in Docker"
- "Ready for real devices—just POST events to our API"

### Backup Plan

If live demo fails:
1. Pre-record screen capture of dashboard interaction
2. Keep screenshots of key views (overview, unit drilldown, device detail)
3. Have `reset-demo.sh` output ready to show instant data regeneration

### Questions to Anticipate

**Q**: "How do you ensure synthetic data is realistic?"  
**A**: "We use statistical distributions—15% miss rate, timing variance of ±30%, device downtime of 8%—all validated against real device logs."

**Q**: "What happens when a real device connects?"  
**A**: "Device POSTs session events via HTTP. Backend stores in PostgreSQL, materialized views update every 5 minutes, dashboard shows mixed real+synthetic data."

**Q**: "How does this scale?"  
**A**: "MVP handles 20 devices fine. For 100+ devices, we'd partition sessions table by month and add Redis caching. PostgreSQL materialized views already pre-aggregate metrics for fast queries."

---

## Next Steps After MVP

1. **Real-time Updates**: Add WebSocket support for live compliance notifications
2. **Export Reports**: PDF/CSV export for compliance audits
3. **Alerting**: Email/Slack notifications for offline devices or compliance drops
4. **Multi-Hospital**: Add hospital entity and tenant isolation
5. **Mobile App**: React Native app for unit managers
6. **Advanced Analytics**: ML-based anomaly detection, predictive maintenance

---

## Resources

- **Spec**: [spec.md](../spec.md)
- **Implementation Plan**: [plan.md](../plan.md)
- **Data Model**: [data-model.md](../data-model.md)
- **API Contracts**: [contracts/api.md](../contracts/api.md)
- **Research**: [research.md](../research.md)

---

## Support

**Issues**: File GitHub issues with `dashboard` label

**Questions**: Contact team on Slack `#deltawash-dashboard`

**Constitution**: All work must align with [.specify/memory/constitution.md](../../.specify/memory/constitution.md)
