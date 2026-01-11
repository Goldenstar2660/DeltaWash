# Research: Hospital Dashboard Technical Decisions

**Feature**: Hospital Dashboard for Handwashing Compliance Analytics  
**Created**: January 10, 2026  
**Purpose**: Document technical decisions, best practices, and integration patterns for dashboard implementation

## Phase 0: Research & Decision Log

### Decision 1: Backend Framework Selection

**Context**: Need Python web framework for REST API with <200ms p95 response times, async support for concurrent users, and strong typing for maintainability.

**Decision**: FastAPI 0.109+

**Rationale**:
- Async-first design enables handling 4+ concurrent users efficiently
- Automatic OpenAPI schema generation simplifies API documentation
- Pydantic integration provides request/response validation with type safety
- Aligns with existing project Python ecosystem (reduces language diversity)
- Production-ready with Uvicorn ASGI server (fast, stable)
- Strong ecosystem for testing (httpx, pytest-asyncio)

**Alternatives Considered**:
- Flask: Simpler but requires extensions for async, lacks built-in validation; FastAPI's async + Pydantic worth the learning curve
- Django + DRF: Overkill for API-only backend; brings ORM, admin, templates we don't need; slower startup for hackathon iteration
- Node.js + Express: Requires introducing JavaScript to backend; team is Python-heavy per existing `src/deltawash_pi/` codebase

**Best Practices**:
- Use dependency injection for database sessions, auth validation (FastAPI `Depends`)
- Separate Pydantic schemas from SQLAlchemy models (schemas/ vs models/)
- Enable CORS for local frontend development (restrict origins in production)
- Use Uvicorn with `--reload` for dev, single worker sufficient for 4 concurrent users

---

### Decision 2: Database Choice and Schema Design

**Context**: Need relational database for structured session/step/heartbeat data with aggregation support; must run in Docker, handle 500+ sessions × 7 days, and support materialized views for <1s query performance.

**Decision**: PostgreSQL 16

**Rationale**:
- Materialized views enable pre-computed aggregates for dashboard queries (compliance trends, averages)
- JSON/JSONB columns support flexible step metadata without schema migrations
- Docker official image with excellent documentation
- ACID guarantees ensure data integrity for compliance analytics
- Window functions, CTEs simplify complex aggregations (e.g., missed step rankings)
- pg_stat_statements for query performance monitoring

**Alternatives Considered**:
- SQLite: Insufficient for concurrent writes from devices + dashboard reads; no materialized views
- MySQL: Lacks robust materialized view support (would require manual trigger-based tables); PostgreSQL window functions more powerful
- MongoDB: NoSQL unnecessary; relational model fits normalized session → steps → devices schema; aggregation pipelines more complex than SQL

**Schema Decisions**:
1. **Normalized Design**: Separate tables for devices, units, sessions, steps, heartbeats, users
   - Reduces duplication (device metadata not repeated per session)
   - Simplifies unit-level filtering (JOIN on unit_id)
2. **Materialized Views for Aggregates**:
   - `mv_daily_compliance`: Pre-compute daily compliance rates per device/unit
   - `mv_step_statistics`: Pre-compute most missed steps, average durations
   - `mv_device_status`: Pre-compute last-seen, heartbeat counts
   - Refresh strategy: Triggered after batch ingestion or on-demand via API call
3. **Indexes**:
   - `sessions(device_id, timestamp)`: Device timeline queries
   - `sessions(unit_id, timestamp)`: Unit drilldown queries
   - `steps(session_id)`: Session detail expansion
   - `heartbeats(device_id, timestamp DESC)`: Last-seen queries
4. **Quality Flags**: Boolean `low_quality` on sessions table; filterable via WHERE clause

**Best Practices**:
- Use Alembic for migrations (version control for schema changes)
- Store timestamps as `TIMESTAMP WITH TIME ZONE` (UTC server-side, convert to local in frontend)
- Use foreign keys with `ON DELETE CASCADE` (deleting device removes orphan sessions)
- Partition sessions table by month if retention grows beyond 30 days (future optimization)

---

### Decision 3: Authentication & Authorization Strategy

**Context**: Four user personas (Org Admin, Analyst, Unit Manager, Technician) with different access levels; must enforce server-side RBAC; hackathon constraints favor simplicity over enterprise SSO.

**Decision**: JWT Bearer Tokens + Server-Side RBAC

**Rationale**:
- Stateless: No session storage required; scales horizontally if needed
- Standard: Frontend can use `Authorization: Bearer <token>` header
- Simple: Library support in FastAPI (`python-jose`, `passlib` for hashing)
- RBAC enforcement: Decode JWT on each request, check user role against endpoint permissions

**Implementation Details**:
1. **User Model**: `users` table with columns: `id`, `email`, `password_hash`, `role` (enum: org_admin, analyst, unit_manager, technician), `unit_id` (nullable; only for unit_manager)
2. **Login Flow**: POST `/api/v1/auth/login` with email+password → returns JWT with claims: `user_id`, `role`, `unit_id`, `exp` (24h expiration)
3. **Token Validation**: FastAPI dependency `get_current_user(token: str = Depends(oauth2_scheme))` decodes JWT, verifies signature, returns user object
4. **Role-Based Access**:
   - All endpoints require authentication (except login)
   - `/api/v1/analytics/overview`: Requires `org_admin` or `analyst`
   - `/api/v1/analytics/unit/{unit_id}`: Requires `org_admin`, `analyst`, or `unit_manager` with matching `unit_id`
   - `/api/v1/devices`: Requires `org_admin` or `technician`
   - `/api/v1/events/*`: Requires `device` role (separate token for device ingestion)
5. **Secret Management**: `JWT_SECRET` from environment variable; generate with `openssl rand -hex 32`

**Alternatives Considered**:
- Session cookies: Requires server-side session store (Redis); adds complexity for hackathon
- OAuth2 / OIDC: Overkill for demo; no external identity provider needed
- API keys: Less secure for user auth; no expiration or role claims built-in

**Best Practices**:
- Hash passwords with bcrypt (passlib default; 12 rounds)
- Use short expiration (24h) + refresh token pattern (defer to post-MVP if needed)
- Store JWT secret in `.env` file; never commit to git
- Frontend stores JWT in `localStorage` (acceptable for MVP; httpOnly cookies better for production)

---

### Decision 4: Frontend Framework and State Management

**Context**: Need SPA for dashboard with charts, filters, real-time updates; TypeScript for type safety; fast dev iteration for hackathon.

**Decision**: React 18 + TypeScript + Vite + React Query

**Rationale**:
- **React 18**: Industry standard, component-based, large ecosystem (chart libraries, UI kits)
- **TypeScript**: Type safety prevents runtime errors; aligns with backend Pydantic schemas
- **Vite**: Fast HMR (<100ms updates); simpler config than Webpack; optimized for hackathon iteration speed
- **React Query (TanStack Query)**: Declarative data fetching, caching, auto-refetch; eliminates manual loading/error state management

**State Management**:
- **React Query**: Server state (analytics data, devices, sessions); handles caching, background refetch
- **React Context**: Client state (auth token, user info, global filters); avoids prop drilling
- **URL Query Params**: Filter state (date range, unit, shift); enables shareable dashboard URLs

**Alternatives Considered**:
- Vue.js: Less familiar to team; React has better chart library ecosystem (Recharts, Victory)
- Angular: Too heavyweight; opinionated framework unnecessary for SPA
- Redux: Overkill for dashboard; React Query + Context sufficient
- Zustand: Good for complex client state; Context + React Query simpler for MVP

**Best Practices**:
- Use React Query `staleTime` to reduce refetch frequency (e.g., 30s for analytics queries)
- Use React Router for page navigation (lazy load pages with `React.lazy`)
- Use Recharts for charts (declarative, responsive, TypeScript support)
- Use Axios with interceptor for auth header injection
- Avoid premature optimization; measure performance before introducing memoization

---

### Decision 5: Synthetic Data Generation Strategy

**Context**: Must generate realistic demo data for 20+ devices, 7+ days, 500+ sessions with variation in compliance, timing, quality flags, and device offline periods. Must support deterministic seeding and configurable parameters.

**Decision**: Python Script with Faker + NumPy for Distributions

**Rationale**:
- Python script can run in backend container or as standalone CLI
- Faker library generates realistic timestamps, device names
- NumPy provides statistical distributions (normal, binomial) for realistic variation
- Deterministic seed enables reproducible demos (same data every reset)

**Implementation Details**:
1. **Parameters** (CLI arguments or config file):
   - `--devices`: Number of devices (default: 20)
   - `--days`: Historical days (default: 7)
   - `--sessions-per-day`: Average sessions per device per day (default: 10)
   - `--miss-rate`: Probability of missing a step (default: 0.15 = 15%)
   - `--low-quality-rate`: Probability of low-quality session (default: 0.12 = 12%)
   - `--offline-rate`: Probability device offline per day (default: 0.08 = 8%)
   - `--seed`: Random seed for reproducibility (default: 42)

2. **Data Generation Logic**:
   - Create `N` devices distributed across 3-5 units (randomly assigned)
   - For each device × day: Generate `sessions_per_day ± 30%` sessions (normal distribution)
   - For each session:
     - Timestamp: Random within day, weighted toward shift hours (7am-3pm: 50%, 3pm-11pm: 35%, 11pm-7am: 15%)
     - Duration: `20-40 seconds` (normal: µ=30, σ=5)
     - Steps: WHO steps 2-7; each step has `miss_rate` chance of being skipped
     - Step durations: Per-step target ± 30% (e.g., step 2: 5-8s, step 3: 8-12s)
     - Quality flag: `low_quality = True` with probability `low_quality_rate`
   - For each device × day: Generate `offline` event with probability `offline_rate` (no heartbeats for 4-12 hours)
   - Heartbeats: Every 5 minutes when device online; includes firmware version (e.g., `v1.2.3`)

3. **Validation**:
   - Assert: Total sessions ≥ 500
   - Assert: At least 3 units exist
   - Assert: At least 20 devices exist
   - Assert: Date range spans exactly `--days` days
   - Assert: Miss rate observed ≈ `--miss-rate ± 5%` (statistical variation acceptable)
   - Assert: Low-quality rate observed ≈ `--low-quality-rate ± 5%`

**Alternatives Considered**:
- CSV/JSON file upload: Requires pre-generating files; less flexible than parameterized script
- Scheduled generator: Unnecessary for hackathon; one-time generation sufficient
- ML-based generation: Overkill; statistical distributions provide sufficient realism

**Best Practices**:
- Use `random.seed(seed)` and `np.random.seed(seed)` for reproducibility
- Log summary statistics after generation (total sessions, devices, compliance rate)
- Store generated data with metadata (seed, parameters) for traceability

---

### Decision 6: Docker Compose Configuration

**Context**: Must run locally on MacOS/Linux/Windows with single command; must support quick reset (wipe + reseed); must isolate backend, frontend, database.

**Decision**: Docker Compose with 3 Services

**Services**:
1. **db**: PostgreSQL 16 official image
   - Volume: `postgres_data` (persistent storage)
   - Port: 5432 (exposed for local psql access)
   - Env: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
   - Health check: `pg_isready` command

2. **backend**: FastAPI + Uvicorn
   - Build: `dashboard/backend/Dockerfile`
   - Depends on: `db` (waits for health check)
   - Port: 8000 (API accessible at `http://localhost:8000`)
   - Env: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`
   - Command: `uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload`
   - Volume: Mount `dashboard/backend/src` for hot reload

3. **frontend**: Vite dev server
   - Build: `dashboard/frontend/Dockerfile`
   - Depends on: `backend`
   - Port: 5173 (SPA accessible at `http://localhost:5173`)
   - Env: `VITE_API_URL=http://localhost:8000`
   - Command: `npm run dev -- --host`
   - Volume: Mount `dashboard/frontend/src` for hot reload

**Scripts**:
- `scripts/start-dashboard.sh`:
  ```bash
  docker-compose up --build
  ```
- `scripts/reset-demo.sh`:
  ```bash
  docker-compose down -v  # Remove volumes
  docker-compose up -d db  # Start DB
  docker-compose run --rm backend python -m src.scripts.init_db  # Create schema
  docker-compose run --rm backend python -m src.scripts.seed_demo_data --seed 42  # Generate data
  docker-compose up backend frontend  # Start services
  ```

**Best Practices**:
- Use `.env` file for secrets (docker-compose reads automatically)
- Use health checks to prevent race conditions (backend waits for DB ready)
- Use volumes for hot reload during development
- Use named volumes for persistent data (`postgres_data`)
- Document port mappings in README

---

### Decision 7: Aggregation Strategy

**Context**: Dashboard queries must return <200ms p95; naive JOINs across 500+ sessions too slow for real-time filtering.

**Decision**: PostgreSQL Materialized Views with Incremental Refresh

**Materialized Views**:

1. **`mv_daily_compliance`**: Daily compliance rate per device/unit
   ```sql
   SELECT
     DATE(s.timestamp) AS date,
     s.device_id,
     d.unit_id,
     COUNT(*) AS total_sessions,
     COUNT(*) FILTER (WHERE s.compliant = TRUE) AS compliant_sessions,
     ROUND(100.0 * COUNT(*) FILTER (WHERE s.compliant = TRUE) / COUNT(*), 2) AS compliance_rate
   FROM sessions s
   JOIN devices d ON s.device_id = d.id
   GROUP BY DATE(s.timestamp), s.device_id, d.unit_id;
   ```

2. **`mv_step_statistics`**: Step-level aggregates
   ```sql
   SELECT
     st.step_id,
     COUNT(*) AS total_attempts,
     COUNT(*) FILTER (WHERE st.completed = FALSE) AS missed_count,
     ROUND(AVG(st.duration_ms), 2) AS avg_duration_ms
   FROM steps st
   GROUP BY st.step_id;
   ```

3. **`mv_device_status`**: Device health summary
   ```sql
   SELECT
     d.id AS device_id,
     d.unit_id,
     MAX(h.timestamp) AS last_seen,
     COUNT(h.id) FILTER (WHERE h.timestamp > NOW() - INTERVAL '24 hours') AS heartbeats_24h,
     CASE WHEN MAX(h.timestamp) < NOW() - INTERVAL '1 hour' THEN TRUE ELSE FALSE END AS is_offline
   FROM devices d
   LEFT JOIN heartbeats h ON d.id = h.device_id
   GROUP BY d.id, d.unit_id;
   ```

**Refresh Strategy**:
- **On-demand**: POST `/api/v1/admin/refresh-aggregates` endpoint triggers `REFRESH MATERIALIZED VIEW CONCURRENTLY`
- **Scheduled**: Cron job (post-MVP) runs refresh every 5 minutes
- **After ingestion**: Batch event ingestion (e.g., backfilling 100+ sessions) triggers refresh automatically

**Query Pattern**:
- Dashboard queries SELECT from materialized views instead of base tables
- Apply filters (date range, unit, quality) as WHERE clauses on materialized views
- Use indexes on materialized views (e.g., `(date, unit_id)`, `(device_id, date)`)

**Alternatives Considered**:
- Real-time aggregation: Fails <200ms p95 requirement for 500+ sessions
- Cached API responses: Requires cache invalidation logic; harder to implement correctly than materialized views
- Pre-aggregated tables with triggers: More complex to maintain than materialized views; triggers add latency to ingestion

**Best Practices**:
- Create indexes on materialized views after initial refresh
- Use `CONCURRENTLY` option to avoid locking during refresh
- Monitor refresh duration; if >10s, consider partitioning base tables
- Document refresh strategy in API documentation

---

### Decision 8: Testing Strategy

**Context**: Hackathon timeline requires prioritization; must validate critical paths (ingestion correctness, aggregation accuracy, dashboard loads).

**Decision**: 3-Tier Testing Approach

**Tier 1: Integration Tests (Backend)** - Priority: HIGH
- **Scope**: Test API endpoints with real DB (TestContainers or test schema)
- **Coverage**:
  - POST `/api/v1/events/session`: Validates session data persisted correctly
  - POST `/api/v1/events/step`: Validates step data linked to session
  - POST `/api/v1/events/heartbeat`: Validates heartbeat data updates device status
  - GET `/api/v1/analytics/overview`: Validates metrics calculated correctly from seed data
  - GET `/api/v1/analytics/unit/{id}`: Validates unit filtering
  - Authentication flow: Login → protected endpoint with JWT
- **Tools**: pytest, httpx, SQLAlchemy fixtures
- **Example**:
  ```python
  def test_session_ingestion_updates_compliance(client, test_db):
      response = client.post("/api/v1/events/session", json={...})
      assert response.status_code == 201
      session = test_db.query(Session).first()
      assert session.compliant == True
  ```

**Tier 2: Unit Tests (Backend + Frontend)** - Priority: MEDIUM
- **Backend**:
  - `test_demo_data_service.py`: Validates synthetic data distributions (miss rate, timing variance)
  - `test_analytics_service.py`: Validates metric calculations with mock data
- **Frontend**:
  - `dateUtils.test.ts`: Validates date range calculations
  - `formatters.test.ts`: Validates duration formatting (e.g., "2m 30s")
- **Tools**: pytest (backend), Vitest (frontend)

**Tier 3: Smoke Tests (Frontend)** - Priority: LOW (defer if time-constrained)
- **Scope**: Validate critical user flows in browser
- **Coverage**:
  - Login → Overview dashboard loads
  - Apply date filter → metrics update
  - Click unit → Unit drilldown loads
- **Tools**: Playwright
- **Example**:
  ```typescript
  test('overview dashboard loads with metrics', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await expect(page.locator('[data-testid="compliance-rate"]')).toBeVisible();
  });
  ```

**What NOT to Test** (defer to post-MVP):
- E2E tests for all filter combinations (combinatorial explosion)
- Performance tests (manual validation sufficient for 4 concurrent users)
- Cross-browser compatibility (Chrome sufficient for demo)

**Best Practices**:
- Use pytest fixtures for test DB setup/teardown
- Use `@pytest.mark.integration` to separate integration from unit tests
- Run integration tests in CI (GitHub Actions) on every PR
- Use Playwright in headed mode during development for debugging

---

## Summary of Resolutions

All [NEEDS CLARIFICATION] markers from Technical Context have been resolved:

1. ✅ **Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend) confirmed
2. ✅ **Primary Dependencies**: FastAPI, PostgreSQL 16, React 18, Vite selected with justification
3. ✅ **Storage**: PostgreSQL with materialized views strategy documented
4. ✅ **Testing**: 3-tier approach (integration > unit > smoke) defined
5. ✅ **Target Platform**: Docker Compose on localhost confirmed
6. ✅ **Performance Goals**: Materialized views + indexes enable <200ms p95
7. ✅ **Constraints**: Single PostgreSQL instance sufficient for 20 devices × 500 sessions
8. ✅ **Scale/Scope**: Confirmed 20 devices, 4 concurrent users, 7+ days retention

**Ready for Phase 1**: Proceed to data-model.md and contracts/ generation.
