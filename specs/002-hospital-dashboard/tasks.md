# Implementation Tasks: Hospital Dashboard for Handwashing Compliance Analytics

**Feature**: `002-hospital-dashboard`  
**Created**: January 10, 2026  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Data Model**: [data-model.md](data-model.md)

## Task Format Legend

```
- [ ] [T###] [P] [US#] Task description with file path

T### = Sequential task ID
[P] = Parallelizable (can run concurrently with other [P] tasks in same phase)
[US#] = User Story label (US1, US2, US3, US4, US5)
```

---

## Phase 1: Setup & Infrastructure

**Goal**: Initialize project structure, Docker environment, and database foundation

**Duration Estimate**: 2-3 hours

### Tasks

- [X] T001 Create dashboard directory structure per plan.md (dashboard/backend/src, dashboard/frontend/src)
- [X] T002 [P] Create backend requirements.txt with FastAPI, SQLAlchemy, Pydantic, python-jose, passlib, psycopg2-binary, alembic, faker, numpy
- [X] T003 [P] Create backend Dockerfile with Python 3.11 base image, install dependencies, expose port 8000
- [X] T004 [P] Create frontend package.json with React 18, TypeScript, Vite, React Query, Recharts, Axios, React Router
- [X] T005 [P] Create frontend Dockerfile with Node 20 base image, install dependencies, expose port 5173
- [X] T006 Create docker-compose.dashboard.yml with 3 services: db (PostgreSQL 16), backend (FastAPI), frontend (Vite)
- [X] T007 Create .env.example with DATABASE_URL, JWT_SECRET, CORS_ORIGINS, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- [X] T008 [P] Create backend config.py to load environment variables and validate configuration
- [X] T009 [P] Create backend database.py with SQLAlchemy engine, session factory, and Base declarative class
- [X] T010 [P] Initialize Alembic in dashboard/backend/alembic/ with env.py configured for SQLAlchemy

**Completion Criteria**:
- ✅ `docker-compose up` successfully starts 3 containers
- ✅ PostgreSQL accepts connections on port 5432
- ✅ Backend health check endpoint returns 200 OK
- ✅ Frontend dev server accessible at http://localhost:5173

---

## Phase 2: Foundational (Blocking Prerequisites)

**Goal**: Database schema, authentication, and base API structure

**Duration Estimate**: 4-5 hours

**Why Foundational**: All user stories depend on database tables and auth; must complete before any user story implementation

### Tasks

- [X] T011 Create SQLAlchemy model for Unit in dashboard/backend/src/models/unit.py with id, unit_name, unit_code, hospital_id, created_at
- [X] T012 [P] Create SQLAlchemy model for Device in dashboard/backend/src/models/device.py with id, unit_id, device_name, firmware_version, installation_date, created_at, updated_at
- [X] T013 [P] Create SQLAlchemy model for Session in dashboard/backend/src/models/session.py with id, device_id, timestamp, duration_ms, compliant, low_quality, missed_steps, config_version, created_at
- [X] T014 [P] Create SQLAlchemy model for Step in dashboard/backend/src/models/step.py with id, session_id, step_id, duration_ms, completed, confidence_score, created_at
- [X] T015 [P] Create SQLAlchemy model for Heartbeat in dashboard/backend/src/models/heartbeat.py with id, device_id, timestamp, firmware_version, online_status, created_at
- [X] T016 [P] Create SQLAlchemy model for User in dashboard/backend/src/models/user.py with id, email, password_hash, role, unit_id, created_at, last_login_at
- [X] T017 Create Alembic migration 001_initial_schema.py to create all tables with indexes and foreign keys per data-model.md
- [X] T018 Create Alembic migration 002_materialized_views.py to create mv_daily_compliance, mv_step_statistics, mv_device_status per data-model.md
- [X] T019 [P] Create Pydantic schema for auth in dashboard/backend/src/schemas/auth.py with LoginRequest, TokenResponse, UserResponse
- [X] T020 [P] Create auth service in dashboard/backend/src/services/auth_service.py with create_access_token, verify_password, hash_password, get_password_hash functions
- [X] T021 Create FastAPI dependency in dashboard/backend/src/dependencies.py with get_db (database session) and get_current_user (JWT validation)
- [X] T022 Create auth router in dashboard/backend/src/api/auth.py with POST /auth/login endpoint
- [X] T023 Create main FastAPI app in dashboard/backend/src/main.py with CORS middleware, router registration, and startup/shutdown events
- [X] T024 Create database initialization script in dashboard/backend/src/scripts/init_db.py to run migrations and verify schema
- [X] T025 Create user creation script in dashboard/backend/src/scripts/create_user.py with CLI arguments for email, password, role, unit_id

**Independent Test Criteria**:
- ✅ Run `docker-compose exec backend alembic upgrade head` successfully creates all tables
- ✅ PostgreSQL contains 6 tables (units, devices, sessions, steps, heartbeats, users) and 3 materialized views
- ✅ POST /auth/login with valid credentials returns JWT token
- ✅ Protected endpoint with invalid token returns 401 Unauthorized
- ✅ create_user.py script creates user with hashed password

---

## Phase 3: User Story 4 - Load Demo Data for Multi-Device Simulation (Priority: P1)

**Goal**: Generate synthetic data to enable dashboard demos without physical devices

**Duration Estimate**: 4-5 hours

**Why P1**: Critical for DeltaHacks demo. Without synthetic data, cannot demonstrate multi-device analytics.

**Independent Test Criteria**:
- ✅ Run seed_demo_data.py generates 20+ devices, 7+ days, 500+ sessions
- ✅ Generated data includes realistic variation (15% miss rate, ±30% timing, 8% downtime)
- ✅ Database queries return expected totals (COUNT(*) FROM sessions >= 500)
- ✅ Materialized views contain aggregated data after generation

### Tasks

- [X] T026 [US4] Create demo data service in dashboard/backend/src/services/demo_data_service.py with generate_synthetic_data function
- [X] T027 [US4] Implement unit generation logic in demo_data_service.py to create 3-5 units with names (ICU, ER, Surgery, Cardiology, Pediatrics)
- [X] T028 [US4] Implement device generation logic in demo_data_service.py to create N devices distributed across units with realistic names and firmware versions
- [X] T029 [US4] Implement session generation logic in demo_data_service.py with configurable miss_rate, low_quality_rate, timing distributions per data-model.md
- [X] T030 [US4] Implement step generation logic in demo_data_service.py to create 6 steps per session (steps 2-7) with realistic durations and completion flags
- [X] T031 [US4] Implement heartbeat generation logic in demo_data_service.py to create heartbeats every 5 minutes with offline periods based on offline_rate
- [X] T032 [US4] Add deterministic seeding with random.seed() and np.random.seed() in demo_data_service.py to ensure reproducible data
- [X] T033 [US4] Implement data validation in demo_data_service.py to assert totals meet minimums (devices >= 20, sessions >= 500, days >= 7)
- [X] T034 [US4] Create seed_demo_data.py CLI script in dashboard/backend/src/scripts/ with arguments: --devices, --days, --sessions-per-day, --miss-rate, --low-quality-rate, --offline-rate, --seed
- [X] T035 [US4] Implement bulk insert optimization in seed_demo_data.py using SQLAlchemy bulk_insert_mappings for performance
- [X] T036 [US4] Add summary logging in seed_demo_data.py to report units_created, devices_created, sessions_created, steps_created, heartbeats_created, date_range
- [X] T037 [US4] Create materialized view refresh script in dashboard/backend/src/scripts/refresh_views.py to run REFRESH MATERIALIZED VIEW CONCURRENTLY for all 3 views
- [X] T038 [US4] Update docker-compose.dashboard.yml to auto-run seed_demo_data.py on first startup (entrypoint script)
- [X] T039 [US4] Create reset-demo.sh script in scripts/ to: docker-compose down -v, docker-compose up -d db, run init_db.py, run seed_demo_data.py --seed 42, docker-compose up backend frontend

**Parallel Opportunities**:
- T026-T031 can be developed in parallel (different functions in same service)
- T034-T036 can be developed in parallel (CLI script while service functions complete)

---

## Phase 4: User Story 5 - Receive Live Device Events (Priority: P2)

**Goal**: Accept HTTP POST events from devices for session, step, and heartbeat data

**Duration Estimate**: 3-4 hours

**Why P2**: Enables integration with real devices. Lower priority than demo data but essential for production.

**Independent Test Criteria**:
- ✅ POST /events/session with valid payload returns 201 Created
- ✅ POST /events/step with valid payload returns 201 Created
- ✅ POST /events/heartbeat with valid payload returns 201 Created
- ✅ POST with invalid payload returns 422 Unprocessable Entity
- ✅ Database contains inserted records after POST requests

### Tasks

- [ ] T040 [US5] Create Pydantic schema for session event in dashboard/backend/src/schemas/session.py with SessionEventRequest, SessionResponse
- [ ] T041 [P] [US5] Create Pydantic schema for step event in dashboard/backend/src/schemas/session.py with StepEventRequest, StepResponse
- [ ] T042 [P] [US5] Create Pydantic schema for heartbeat event in dashboard/backend/src/schemas/device.py with HeartbeatEventRequest, HeartbeatResponse
- [ ] T043 [US5] Create ingestion router in dashboard/backend/src/api/ingestion.py with POST /events/session endpoint
- [ ] T044 [US5] Implement session ingestion logic in ingestion.py to validate payload, insert into sessions table, handle errors
- [ ] T045 [US5] Add POST /events/step endpoint in ingestion.py to insert step records linked to session_id
- [ ] T046 [US5] Add POST /events/heartbeat endpoint in ingestion.py to insert heartbeat records and update device last_seen
- [ ] T047 [P] [US5] Create integration test in dashboard/backend/tests/integration/test_ingestion.py for POST /events/session with valid/invalid payloads
- [ ] T048 [P] [US5] Add integration test in test_ingestion.py for POST /events/step with valid session_id and invalid session_id (404)
- [ ] T049 [P] [US5] Add integration test in test_ingestion.py for POST /events/heartbeat with valid device_id
- [ ] T050 [US5] Register ingestion router in main.py with /api/v1/events prefix

**Parallel Opportunities**:
- T040-T042 (Pydantic schemas) can be developed concurrently
- T047-T049 (integration tests) can be written in parallel after endpoints exist

---

## Phase 5: User Story 1 - View Organization-Wide Compliance Overview (Priority: P1)

**Goal**: Display org-wide analytics with compliance trends, missed steps, avg times, quality rate, device status

**Duration Estimate**: 6-8 hours

**Why P1**: Primary value proposition for executives and analysts. Core dashboard functionality.

**Independent Test Criteria**:
- ✅ GET /analytics/overview returns compliance_trend, most_missed_step, average_wash_time_ms, average_step_times, quality_rate, device_summary
- ✅ Date range filter (date_from, date_to) correctly scopes metrics
- ✅ Unit filter (unit_id) correctly scopes metrics
- ✅ Shift filter (shift) correctly scopes metrics to time buckets
- ✅ Quality toggle (exclude_low_quality) excludes flagged sessions
- ✅ Frontend displays all metrics and updates when filters change

### Backend Tasks

- [X] T051 [US1] Create Pydantic schema for analytics in dashboard/backend/src/schemas/analytics.py with OverviewResponse, ComplianceTrendItem, MostMissedStep, AverageStepTime, DeviceSummary
- [X] T052 [US1] Create analytics service in dashboard/backend/src/services/analytics_service.py with get_overview_analytics function
- [X] T053 [US1] Implement compliance_trend calculation in analytics_service.py by querying mv_daily_compliance with date/unit/shift filters
- [X] T054 [US1] Implement most_missed_step calculation in analytics_service.py by querying mv_step_statistics and ranking by miss_count
- [X] T055 [US1] Implement average_wash_time calculation in analytics_service.py by querying sessions table with AVG(duration_ms)
- [X] T056 [US1] Implement average_step_times calculation in analytics_service.py by querying mv_step_statistics grouped by step_id
- [X] T057 [US1] Implement quality_rate calculation in analytics_service.py by counting non-low_quality sessions percentage
- [X] T058 [US1] Implement device_summary calculation in analytics_service.py by querying mv_device_status for total/online/offline counts
- [X] T059 [US1] Add shift filtering logic in analytics_service.py to convert shift enum (morning/afternoon/night) to time ranges (7am-3pm, 3pm-11pm, 11pm-7am)
- [X] T060 [US1] Create analytics router in dashboard/backend/src/api/analytics.py with GET /analytics/overview endpoint
- [X] T061 [US1] Implement query parameter validation in analytics router for date_from (required), date_to (required), unit_id (optional), shift (optional), exclude_low_quality (optional)
- [X] T062 [US1] Register analytics router in main.py with /api/v1/analytics prefix
- [X] T063 [P] [US1] Create integration test in dashboard/backend/tests/integration/test_analytics.py for GET /analytics/overview with seed data
- [X] T064 [P] [US1] Add integration test for date range filtering in test_analytics.py
- [X] T065 [P] [US1] Add integration test for unit filtering in test_analytics.py
- [X] T066 [P] [US1] Add integration test for shift filtering in test_analytics.py
- [X] T067 [P] [US1] Add integration test for quality toggle in test_analytics.py

### Frontend Tasks

- [X] T068 [P] [US1] Create TypeScript types in dashboard/frontend/src/types/analytics.ts for OverviewResponse, ComplianceTrendItem, MostMissedStep, etc.
- [X] T069 [P] [US1] Create Axios instance in dashboard/frontend/src/services/api.ts with baseURL, auth interceptor for JWT token
- [X] T070 [US1] Create analytics API client in dashboard/frontend/src/services/analyticsApi.ts with fetchOverviewAnalytics function
- [X] T071 [P] [US1] Create React Query hook in dashboard/frontend/src/hooks/useAnalytics.ts for overview analytics with query key, staleTime 30s
- [X] T072 [P] [US1] Create FilterContext in dashboard/frontend/src/context/FilterContext.tsx to manage dateFrom, dateTo, unitId, shift, excludeLowQuality state
- [X] T073 [P] [US1] Create DateRangeFilter component in dashboard/frontend/src/components/filters/DateRangeFilter.tsx with presets (last 24h, 7d, 30d, custom)
- [X] T074 [P] [US1] Create UnitFilter component in dashboard/frontend/src/components/filters/UnitFilter.tsx with multi-select dropdown
- [X] T075 [P] [US1] Create ShiftFilter component in dashboard/frontend/src/components/filters/ShiftFilter.tsx with morning/afternoon/night buttons
- [X] T076 [P] [US1] Create QualityToggle component in dashboard/frontend/src/components/filters/QualityToggle.tsx with checkbox
- [X] T077 [P] [US1] Create MetricCard component in dashboard/frontend/src/components/common/MetricCard.tsx to display label + value + change indicator
- [X] T078 [P] [US1] Create ComplianceTrendChart component in dashboard/frontend/src/components/charts/ComplianceTrendChart.tsx using Recharts LineChart
- [X] T079 [P] [US1] Create StepBarChart component in dashboard/frontend/src/components/charts/StepBarChart.tsx using Recharts BarChart for missed steps
- [X] T080 [P] [US1] Create TimingChart component in dashboard/frontend/src/components/charts/TimingChart.tsx using Recharts BarChart for avg step times
- [X] T081 [P] [US1] Create DeviceStatusBadge component in dashboard/frontend/src/components/common/DeviceStatusBadge.tsx with online/offline indicator
- [X] T082 [US1] Create OverviewPage component in dashboard/frontend/src/pages/OverviewPage.tsx that uses FilterContext, useAnalytics hook, and renders all metric cards + charts
- [X] T083 [US1] Wire up filter changes in OverviewPage.tsx to trigger React Query refetch with new parameters
- [X] T084 [P] [US1] Add loading state handling in OverviewPage.tsx with Loader component
- [X] T085 [P] [US1] Add error state handling in OverviewPage.tsx with error message display
- [X] T086 [P] [US1] Add empty state handling in OverviewPage.tsx when no data matches filters

**Parallel Opportunities**:
- T051-T058 (backend analytics calculations) can be developed in parallel (different functions)
- T063-T067 (integration tests) can be written concurrently
- T068-T081 (frontend components) can be developed in parallel teams (filters, charts, metrics)

---

## Phase 6: User Story 2 - Drill Down into Unit Performance (Priority: P2)

**Goal**: Display unit-scoped metrics and device leaderboard

**Duration Estimate**: 4-5 hours

**Why P2**: Enables unit managers to monitor their teams. Builds on overview analytics infrastructure.

**Independent Test Criteria**:
- ✅ GET /analytics/unit/{unit_id} returns unit-scoped metrics and device leaderboard
- ✅ Unit manager with matching unit_id can access endpoint (RBAC)
- ✅ Unit manager with different unit_id receives 403 Forbidden
- ✅ Frontend displays unit page with leaderboard and filtering

### Backend Tasks

- [X] T087 [US2] Create Pydantic schema for unit analytics in dashboard/backend/src/schemas/analytics.py with UnitResponse, UnitMetrics, DeviceLeaderboardItem
- [X] T088 [US2] Create get_unit_analytics function in analytics_service.py to calculate unit-scoped compliance_trend, most_missed_step, average_times, quality_rate
- [X] T089 [US2] Implement device leaderboard calculation in analytics_service.py by querying mv_daily_compliance grouped by device_id, ordered by compliance_rate DESC
- [X] T090 [US2] Add rank calculation in device leaderboard with ROW_NUMBER() window function or Python enumeration
- [X] T091 [US2] Add GET /analytics/unit/{unit_id} endpoint in analytics router with path parameter and query parameters (date_from, date_to, shift, exclude_low_quality)
- [X] T092 [US2] Implement RBAC check in GET /analytics/unit/{unit_id} to allow org_admin, analyst, or unit_manager with matching unit_id only
- [X] T093 [P] [US2] Create integration test in test_analytics.py for GET /analytics/unit/{unit_id} with org_admin token
- [X] T094 [P] [US2] Add integration test for unit_manager RBAC (matching unit_id passes, different unit_id fails with 403)

### Frontend Tasks

- [X] T095 [P] [US2] Create TypeScript types in dashboard/frontend/src/types/analytics.ts for UnitResponse, DeviceLeaderboardItem
- [X] T096 [US2] Create fetchUnitAnalytics function in analyticsApi.ts with unitId parameter
- [X] T097 [US2] Create useUnitAnalytics hook in useAnalytics.ts for unit-scoped analytics
- [X] T098 [P] [US2] Create DeviceLeaderboard component in dashboard/frontend/src/components/DeviceLeaderboard.tsx with table showing device_name, compliance_rate, rank, visual indicators
- [X] T099 [US2] Create UnitPage component in dashboard/frontend/src/pages/UnitPage.tsx that reuses metric cards + charts from OverviewPage but scoped to unit
- [X] T100 [US2] Add React Router route in App.tsx for /units/:unitId → UnitPage
- [X] T101 [US2] Add navigation link from OverviewPage to UnitPage when clicking on unit filter selection

**Parallel Opportunities**:
- T087-T090 (backend analytics) can be developed concurrently with T095-T098 (frontend components)
- T093-T094 (integration tests) can be written in parallel

---

## Phase 7: User Story 3 - Monitor Individual Device Health (Priority: P2)

**Goal**: Display device operational status, heartbeat metrics, reliability flags

**Duration Estimate**: 3-4 hours

**Why P2**: Enables technicians to prioritize maintenance. Complements unit leaderboard.

**Independent Test Criteria**:
- ✅ GET /analytics/device/{device_id} returns device status, performance, reliability_flags
- ✅ GET /devices lists all devices with last_seen, is_online status
- ✅ GET /devices/{device_id} returns detailed device information
- ✅ Frontend displays device page with metrics and reliability warnings

### Backend Tasks

- [X] T102 [US3] Create Pydantic schema for device analytics in dashboard/backend/src/schemas/analytics.py with DeviceResponse, DeviceStatus, DevicePerformance, ReliabilityFlag
- [X] T103 [US3] Create Pydantic schema for device in dashboard/backend/src/schemas/device.py with DeviceListItem, DeviceDetail
- [X] T104 [US3] Create get_device_analytics function in analytics_service.py to query device status from mv_device_status and performance from sessions
- [X] T105 [US3] Implement reliability_flags generation in analytics_service.py to detect offline_period (last_seen > 1 hour), low_heartbeat_rate (<80% expected)
- [X] T106 [US3] Add GET /analytics/device/{device_id} endpoint in analytics router with query parameters (date_from, date_to)
- [X] T107 [US3] Create devices router in dashboard/backend/src/api/devices.py with GET /devices endpoint (list all)
- [X] T108 [US3] Add GET /devices/{device_id} endpoint in devices router for device detail
- [X] T109 [US3] Register devices router in main.py with /api/v1/devices prefix
- [X] T110 [P] [US3] Create integration test in dashboard/backend/tests/integration/test_devices.py for GET /devices
- [X] T111 [P] [US3] Add integration test in test_analytics.py for GET /analytics/device/{device_id}

### Frontend Tasks

- [X] T112 [P] [US3] Create TypeScript types in dashboard/frontend/src/types/device.ts for DeviceResponse, DeviceStatus, ReliabilityFlag
- [X] T113 [US3] Create devicesApi.ts in services/ with fetchDevices, fetchDeviceDetail, fetchDeviceAnalytics functions
- [X] T114 [US3] Create useDevices hook in dashboard/frontend/src/hooks/useDevices.ts for device list and detail queries
- [X] T115 [P] [US3] Create DeviceStatusCard component in dashboard/frontend/src/components/DeviceStatusCard.tsx to display last_seen, heartbeats_24h, uptime percentage
- [X] T116 [P] [US3] Create ReliabilityFlags component in dashboard/frontend/src/components/ReliabilityFlags.tsx to display warnings with severity colors
- [X] T117 [US3] Create DevicePage component in dashboard/frontend/src/pages/DevicePage.tsx with device info, status, performance, reliability flags
- [X] T118 [US3] Add React Router route in App.tsx for /devices/:deviceId → DevicePage
- [X] T119 [US3] Add navigation link from DeviceLeaderboard to DevicePage when clicking device name

**Parallel Opportunities**:
- T102-T105 (backend analytics) can be developed concurrently with T112-T116 (frontend components)
- T110-T111 (integration tests) can be written in parallel

---

## Phase 8: Authentication & Authorization

**Goal**: Complete auth flow with login page, token storage, protected routes

**Duration Estimate**: 3-4 hours

**Why Separate Phase**: Auth spans multiple user stories; foundational work done in Phase 2, UI integration done here

**Independent Test Criteria**:
- ✅ Login page accepts email/password and stores JWT token
- ✅ Protected routes redirect to login if no token
- ✅ Auth header included in all API requests
- ✅ Token expiration handled gracefully with logout

### Tasks

- [ ] T120 Create AuthContext in dashboard/frontend/src/context/AuthContext.tsx to manage user state, login, logout functions
- [ ] T121 Create authApi.ts in services/ with login function that POSTs to /auth/login
- [ ] T122 Create useAuth hook in dashboard/frontend/src/hooks/useAuth.ts to access AuthContext
- [ ] T123 [P] Create LoginPage component in dashboard/frontend/src/pages/LoginPage.tsx with email/password form
- [ ] T124 Update api.ts Axios interceptor to read token from localStorage and add to Authorization header
- [ ] T125 Add Axios response interceptor in api.ts to handle 401 errors by clearing token and redirecting to login
- [ ] T126 Create ProtectedRoute component in dashboard/frontend/src/components/ProtectedRoute.tsx that checks auth state
- [ ] T127 Update App.tsx to wrap protected routes (overview, unit, device pages) with ProtectedRoute component
- [ ] T128 Create Header component in dashboard/frontend/src/components/layout/Header.tsx with logout button and user email display
- [ ] T129 Create Layout component in dashboard/frontend/src/components/layout/Layout.tsx with Header and main content area

**Parallel Opportunities**:
- T123-T124 (LoginPage + interceptor) can be developed concurrently
- T126-T129 (route protection + layout) can be developed in parallel

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Production readiness, error handling, responsive design, performance optimization

**Duration Estimate**: 4-5 hours

### Tasks

- [ ] T130 Add global error boundary in App.tsx to catch React errors and display fallback UI
- [ ] T131 [P] Create Loader component in dashboard/frontend/src/components/common/Loader.tsx with spinner animation
- [ ] T132 [P] Create ErrorMessage component in dashboard/frontend/src/components/common/ErrorMessage.tsx with retry button
- [ ] T133 [P] Add responsive CSS to all components using media queries for tablet/desktop breakpoints
- [ ] T134 Add empty state components for "No data available" in OverviewPage, UnitPage, DevicePage
- [ ] T135 Implement debounced filter updates in FilterContext to reduce API calls during rapid filter changes
- [ ] T136 Add admin endpoint POST /admin/refresh-aggregates in dashboard/backend/src/api/admin.py to manually trigger materialized view refresh
- [ ] T137 [P] Add admin endpoint POST /admin/demo-data/generate in admin router to trigger seed_demo_data via API (alternative to CLI)
- [ ] T138 [P] Add admin endpoint DELETE /admin/demo-data/wipe in admin router to truncate all tables
- [ ] T139 Add RBAC check to admin endpoints requiring org_admin role
- [ ] T140 Create Sidebar component in dashboard/frontend/src/components/layout/Sidebar.tsx with navigation links (Overview, Units, Devices)
- [ ] T141 Update Layout component to include Sidebar
- [ ] T142 Add dark mode toggle in Header component with localStorage persistence (optional enhancement)
- [ ] T143 [P] Add backend logging configuration in main.py with structured logs (JSON format) for production
- [ ] T144 [P] Add API request logging middleware in main.py to log all requests with duration, status code, path
- [ ] T145 Add health check endpoint GET /health in main.py that checks database connection
- [ ] T146 Update docker-compose.dashboard.yml to add health checks for backend (GET /health) and db (pg_isready)
- [ ] T147 Create start-dashboard.sh script in scripts/ with docker-compose up --build command
- [ ] T148 Update README.md in repository root with dashboard quickstart instructions (link to quickstart.md)

**Parallel Opportunities**:
- T131-T133 (common UI components) can be developed concurrently
- T136-T139 (admin endpoints) can be developed in parallel
- T143-T144 (logging) can be added in parallel

---

## Dependencies & Execution Order

### Critical Path (Must Complete in Order)

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US4: Demo Data) → Phase 5 (US1: Overview Dashboard)
```

**Reasoning**:
- Phase 1 required for Docker environment
- Phase 2 required for database schema + auth foundation
- Phase 3 (US4) required for demo data to test dashboard
- Phase 5 (US1) is primary value; overview must work first

### Parallel Execution Opportunities

**After Phase 2 Completes**:
- Phase 3 (US4: Demo Data)
- Phase 4 (US5: Live Ingestion) - can develop in parallel with demo data

**After Phase 5 Completes**:
- Phase 6 (US2: Unit Drilldown) - reuses overview components
- Phase 7 (US3: Device Health) - independent of unit drilldown
- Phase 8 (Auth UI) - independent of analytics pages

**Phase 9 (Polish)** can start anytime after Phase 5 for incremental improvements

### User Story Completion Order

1. **US4** (P1) - Demo Data Generation → Enables testing
2. **US1** (P1) - Overview Dashboard → Primary value proposition
3. **US5** (P2) - Live Ingestion → Enables real device integration
4. **US2** (P2) - Unit Drilldown → Extends overview with unit scoping
5. **US3** (P2) - Device Health → Completes monitoring capabilities

### Suggested Team Allocation (if parallel teams available)

**Team A (Backend Focus)**:
- Phase 2: Database schema + auth
- Phase 3: Demo data generation
- Phase 4: Live ingestion endpoints

**Team B (Frontend Focus)**:
- Phase 1: Frontend setup
- Phase 5: Overview dashboard UI
- Phase 8: Auth UI integration

**Team C (Full-Stack)**:
- Phase 6: Unit drilldown (backend + frontend)
- Phase 7: Device health (backend + frontend)
- Phase 9: Polish & cross-cutting

---

## Testing Strategy

### Integration Tests (Priority: HIGH)

**Coverage**:
- All API endpoints with valid/invalid payloads
- RBAC enforcement (user roles accessing restricted endpoints)
- Filter combinations (date range + unit + shift + quality)
- Demo data generation with validation

**Test Files**:
- `dashboard/backend/tests/integration/test_ingestion.py` (T047-T049)
- `dashboard/backend/tests/integration/test_analytics.py` (T063-T067, T093-T094, T111)
- `dashboard/backend/tests/integration/test_devices.py` (T110)
- `dashboard/backend/tests/integration/test_auth.py` (Phase 2, not explicitly tasked)

**Run Command**:
```bash
docker-compose exec backend pytest tests/integration/ -v
```

### Unit Tests (Priority: MEDIUM)

**Coverage**:
- Demo data service distribution validation (miss rates, timing variance)
- Analytics service metric calculations with mock data
- Frontend utility functions (date formatting, duration display)

**Test Files**:
- `dashboard/backend/tests/unit/test_demo_data_service.py` (not explicitly tasked)
- `dashboard/backend/tests/unit/test_analytics_service.py` (not explicitly tasked)
- `dashboard/frontend/tests/unit/dateUtils.test.ts` (not explicitly tasked)
- `dashboard/frontend/tests/unit/formatters.test.ts` (not explicitly tasked)

**Run Command**:
```bash
# Backend
docker-compose exec backend pytest tests/unit/ -v

# Frontend
docker-compose exec frontend npm run test
```

### Smoke Tests (Priority: LOW - defer if time-constrained)

**Coverage**:
- Login → Overview dashboard loads
- Apply date filter → metrics update
- Navigate to Unit page → unit metrics load

**Test File**:
- `dashboard/frontend/tests/smoke/dashboard.spec.ts` (not explicitly tasked)

**Run Command**:
```bash
cd dashboard/frontend
npx playwright test
```

---

## Implementation Strategy

### MVP First (Minimum Viable Product)

**Core MVP** = User Story 1 + User Story 4 only

**Justification**: With just overview dashboard (US1) and demo data (US4), you can demonstrate full analytics capabilities at DeltaHacks. Unit drilldown (US2) and device health (US3) are enhancements.

**MVP Timeline**: Phases 1 + 2 + 3 + 5 + 8 (auth) = ~16-20 hours

**MVP Deliverable**:
- ✅ Docker compose stack running
- ✅ Synthetic data with 20 devices, 7 days, 500+ sessions
- ✅ Overview dashboard with all metrics
- ✅ Filters working (date, unit, shift, quality)
- ✅ Login + protected routes

### Incremental Delivery

**Iteration 1** (MVP): Phases 1-3, 5, 8  
**Iteration 2** (Enhanced): Add Phase 4 (live ingestion) + Phase 6 (unit drilldown)  
**Iteration 3** (Complete): Add Phase 7 (device health) + Phase 9 (polish)

### Hackathon Time Constraints

**If 24 hours available**:
- Focus on MVP (Phases 1-3, 5, 8)
- Defer unit drilldown, device health, polish
- Manually test instead of writing integration tests

**If 48 hours available**:
- Complete MVP + add Phase 4 (live ingestion) + Phase 6 (unit drilldown)
- Add integration tests for critical paths

**If 72+ hours available**:
- Complete all phases including polish
- Full test coverage

---

## Task Summary

**Total Tasks**: 148  
**Parallelizable Tasks**: 52 (marked with [P])

**By Phase**:
- Phase 1 (Setup): 10 tasks
- Phase 2 (Foundational): 15 tasks
- Phase 3 (US4: Demo Data): 14 tasks
- Phase 4 (US5: Live Ingestion): 11 tasks
- Phase 5 (US1: Overview Dashboard): 36 tasks (backend + frontend)
- Phase 6 (US2: Unit Drilldown): 15 tasks
- Phase 7 (US3: Device Health): 18 tasks
- Phase 8 (Auth UI): 10 tasks
- Phase 9 (Polish): 19 tasks

**By User Story**:
- US1 (Overview Dashboard): 36 tasks
- US2 (Unit Drilldown): 15 tasks
- US3 (Device Health): 18 tasks
- US4 (Demo Data): 14 tasks
- US5 (Live Ingestion): 11 tasks
- Infrastructure/Cross-cutting: 54 tasks

**Estimated Duration**: 30-40 hours total (1-2 engineers, 2-3 days)

---

## Next Actions

1. ✅ Review this task breakdown with team
2. ✅ Confirm MVP scope (recommend Phases 1-3, 5, 8)
3. ✅ Assign tasks to engineers (if parallel teams)
4. ✅ Create GitHub issues from tasks (optional: use `/speckit.taskstoissues`)
5. ✅ Begin Phase 1: Setup & Infrastructure

**Ready to implement**: All tasks have clear file paths, acceptance criteria, and dependencies documented.
