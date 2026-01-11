# Implementation Plan: Hospital Dashboard for Handwashing Compliance Analytics

**Branch**: `002-hospital-dashboard` | **Date**: January 10, 2026 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/002-hospital-dashboard/spec.md`

## Summary

Build a web-based analytics dashboard for hospitals to monitor handwashing compliance across multiple devices and units. The system must support both live device data ingestion and synthetic demo data generation to enable DeltaHacks demonstrations with a single physical device. The dashboard provides organization-wide overview metrics, unit-level drilldowns, and device health monitoring with flexible filtering by date range, unit, shift, and quality flags. Core value: enable compliance officers and unit managers to identify trends, problem areas, and device issues across 20+ devices and 7+ days of historical data.

**Technical Approach**: Python FastAPI backend with PostgreSQL database, React+TypeScript (Vite) frontend, containerized with docker-compose for local development and demo deployment. JWT-based authentication with server-side RBAC. Synthetic data generation uses deterministic seeding with configurable parameters for realistic variation.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend), Node.js 20.x (frontend build)  
**Primary Dependencies**: FastAPI 0.109+, SQLAlchemy 2.0+, Pydantic 2.x, PostgreSQL 16, React 18, React Query, Recharts, Vite 5  
**Storage**: PostgreSQL 16 with materialized views for aggregated metrics; no external caching layer for MVP  
**Testing**: pytest + httpx (backend integration), pytest (synthetic data validation), Vitest (frontend unit), Playwright (frontend smoke)  
**Target Platform**: Docker containers running on localhost (MacOS/Linux/Windows with Docker Desktop); accessible via browser on same machine  
**Project Type**: Web application (backend API + frontend SPA)  
**Performance Goals**: <3s page load for 20 devices × 500 sessions, <1s filter updates, <30s synthetic data generation for full dataset  
**Constraints**: <200ms p95 API response for dashboard queries, <5s latency for device event ingestion, single PostgreSQL instance (no distributed DB)  
**Scale/Scope**: 20 devices, ~1000 sessions/day, 4 concurrent dashboard users, 7+ days historical data retention (unlimited for MVP)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Initial)

**Principle: Spec-Driven Scope Discipline**
- ✅ PASS: All dashboard features trace to FR-001 through FR-020 in spec.md
- ✅ PASS: No speculative features; demo data generation is explicitly required (FR-004, FR-005, FR-006, FR-007)
- ⚠️ POTENTIAL VIOLATION: Adding new web application + database + frontend introduces significant scope beyond original on-device detection system
  - **Justification**: This feature is a separate component that consumes device events rather than modifying detection logic; it does not alter WHO step detection, camera pipeline, or on-device state machine
  - **Impact**: Dashboard runs as standalone service; device code in `src/deltawash_pi/` remains unchanged except for adding HTTP client to post events
  - **Mitigation**: Keep dashboard code in separate top-level directories (`dashboard/backend/`, `dashboard/frontend/`) to maintain clean separation

**Principle: Modular On-Device Architecture**
- ✅ PASS: Dashboard does not modify detector modules, state machine, or MediaPipe pipeline
- ⚠️ POTENTIAL VIOLATION: Requires device to send HTTP events
  - **Justification**: Existing `src/deltawash_pi/logging/sessions.py` already persists session data locally; adding HTTP POST is minimal extension to logging layer
  - **Impact**: Device gains optional HTTP client in logging layer; detection logic unaffected
  - **Mitigation**: HTTP posting is opt-in via config; device remains fully functional without dashboard

**Principle: Real-Time Reliability & Fail-Safe Operation**
- ✅ PASS: Device HTTP posting must fail gracefully (FR-004 acceptance scenario 4); WiFi failures must not crash detection
- ✅ PASS: Dashboard accepts batch processing with up to 5s latency (spec: Assumptions section)
- ✅ PASS: Dashboard does not interfere with device real-time performance

**Principle: Observability & Analytics**
- ✅ PASS: Dashboard extends observability by aggregating device logs across multiple units
- ✅ PASS: All session records include device ID, timestamp, config version (inherits from existing device logging)
- ⚠️ POTENTIAL VIOLATION: Dashboard stores data in PostgreSQL instead of local files
  - **Justification**: Aggregating data from 20+ devices requires centralized storage; local per-device files are insufficient for org-wide analytics
  - **Impact**: Device continues local logging unchanged; dashboard provides additive analytics layer
  - **Mitigation**: Device logging remains primary source of truth; dashboard is read-only analytics tool

**Principle: Verification, Privacy & Demo Readiness**
- ✅ PASS: No video storage (spec: Out of Scope)
- ✅ PASS: No staff identity tracking (spec: Out of Scope)
- ✅ PASS: Demo mode with synthetic data generation (FR-004, FR-005, FR-006, FR-007)
- ✅ PASS: No cloud services; runs locally via docker-compose
- ✅ PASS: Privacy-first: only metadata and step completion data persisted

**Initial Verdict**: ⚠️ CONDITIONAL PASS with justifications for adding new web application component. Dashboard is additive analytics layer that does not violate core detection principles. Re-evaluate after Phase 1 design to ensure device integration remains minimal.

### Gates Summary

| Gate | Status | Notes |
|------|--------|-------|
| No spec violations | ⚠️ CONDITIONAL | Dashboard adds new component but aligns with spec |
| Modular architecture preserved | ✅ PASS | Device detection logic unmodified |
| Fail-safe operation | ✅ PASS | HTTP posting fails gracefully |
| Privacy & demo readiness | ✅ PASS | No cloud, no identity, demo-ready |

**Action Required**: Proceed to Phase 0 research. Re-check after Phase 1 design validates minimal device integration.

---

### Post-Design Evaluation (After Phase 1)

**Re-evaluation Status**: ✅ PASS with confirmed justifications

**Principle: Spec-Driven Scope Discipline**
- ✅ CONFIRMED: All dashboard features documented in data-model.md and contracts/api.md trace to spec requirements
- ✅ CONFIRMED: No speculative features added; all entities (Device, Unit, Session, Step, Heartbeat, User) map directly to functional requirements
- ✅ CONFIRMED: Dashboard remains isolated in `dashboard/` directory structure; device code separation maintained

**Principle: Modular On-Device Architecture**
- ✅ CONFIRMED: Device integration limited to adding HTTP client in `src/deltawash_pi/logging/` (existing logging layer)
- ✅ CONFIRMED: Device detectors, state machine, MediaPipe pipeline remain unchanged
- ✅ CONFIRMED: HTTP posting is opt-in via config; device operates independently without dashboard

**Principle: Real-Time Reliability & Fail-Safe Operation**
- ✅ CONFIRMED: API contracts specify fail-safe error handling (500 errors for DB failures)
- ✅ CONFIRMED: Batch processing with up to 5s latency documented in research.md
- ✅ CONFIRMED: Device HTTP client will catch exceptions and log errors without crashing detection pipeline

**Principle: Observability & Analytics**
- ✅ CONFIRMED: Data model includes device_id, timestamp, config_version for full traceability
- ✅ CONFIRMED: Session logging schema extends device local logs to centralized PostgreSQL
- ✅ CONFIRMED: Materialized views provide aggregated analytics without modifying device behavior

**Principle: Verification, Privacy & Demo Readiness**
- ✅ CONFIRMED: No video storage (Out of Scope in spec.md)
- ✅ CONFIRMED: No staff identity fields in data model
- ✅ CONFIRMED: Synthetic data generation fully specified in research.md with deterministic seeding
- ✅ CONFIRMED: All services run locally via docker-compose (no cloud dependencies)
- ✅ CONFIRMED: Demo reset script documented in quickstart.md

**Final Verdict**: ✅ FULL PASS. Dashboard implementation aligns with all constitution principles. Device integration is minimal (HTTP client only) and dashboard operates as additive analytics layer without modifying core detection logic.

### Updated Gates Summary

| Gate | Initial Status | Post-Design Status | Notes |
|------|----------------|-------------------|-------|
| No spec violations | ⚠️ CONDITIONAL | ✅ PASS | All features traced to spec |
| Modular architecture preserved | ✅ PASS | ✅ PASS | Device detection unchanged |
| Fail-safe operation | ✅ PASS | ✅ PASS | Error handling specified |
| Privacy & demo readiness | ✅ PASS | ✅ PASS | No cloud, synthetic data ready |

**Approval**: Ready to proceed with implementation (Phase 2: `/speckit.tasks`).

## Project Structure

### Documentation (this feature)

```text
specs/002-hospital-dashboard/
├── plan.md              # This file
├── research.md          # Phase 0 output: tech decisions, best practices
├── data-model.md        # Phase 1 output: entities, relationships, schemas
├── quickstart.md        # Phase 1 output: local setup, demo data generation
├── contracts/           # Phase 1 output: API specifications
│   └── api.md          # OpenAPI-style HTTP endpoint contracts
├── checklists/
│   └── requirements.md # Specification quality validation (already exists)
└── tasks.md            # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Existing device code (unchanged by this feature except minimal HTTP client addition)
src/deltawash_pi/
├── cli/                # Existing device CLI commands
├── detectors/          # Existing WHO step detectors (UNCHANGED)
├── interpreter/        # Existing state machine (UNCHANGED)
├── feedback/           # Existing ESP8266 LED driver (UNCHANGED)
├── logging/            # Add HTTP event posting to existing session logger
└── config/             # Existing config loader (UNCHANGED)

# New dashboard backend API
dashboard/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI application entry point
│   │   ├── config.py              # Environment configuration (DB URL, JWT secret)
│   │   ├── database.py            # SQLAlchemy engine, session management
│   │   ├── dependencies.py        # FastAPI dependencies (auth, DB session)
│   │   ├── models/                # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── device.py          # Device model
│   │   │   ├── unit.py            # Unit model
│   │   │   ├── session.py         # Session model
│   │   │   ├── step.py            # Step model
│   │   │   ├── heartbeat.py       # Heartbeat model
│   │   │   └── user.py            # User model (RBAC)
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── device.py          # Device DTOs
│   │   │   ├── session.py         # Session DTOs
│   │   │   ├── analytics.py       # Analytics response DTOs
│   │   │   └── auth.py            # Auth DTOs (login, token)
│   │   ├── api/                   # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── ingestion.py       # POST /api/v1/events/session, /step, /heartbeat
│   │   │   ├── analytics.py       # GET /api/v1/analytics/overview, /unit/{id}, /device/{id}
│   │   │   ├── devices.py         # GET /api/v1/devices, /devices/{id}
│   │   │   └── auth.py            # POST /api/v1/auth/login
│   │   ├── services/              # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── analytics_service.py    # Compute metrics, query aggregates
│   │   │   ├── demo_data_service.py    # Generate synthetic data
│   │   │   └── auth_service.py         # JWT creation, validation
│   │   ├── repositories/          # Data access layer (optional for MVP, see Complexity Tracking)
│   │   │   ├── __init__.py
│   │   │   ├── session_repository.py
│   │   │   └── analytics_repository.py
│   │   └── scripts/               # Utility scripts
│   │       ├── __init__.py
│   │       ├── init_db.py         # Create tables, materialized views
│   │       ├── seed_demo_data.py  # CLI for synthetic data generation
│   │       └── create_user.py     # CLI for creating dashboard users
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── integration/
│   │   │   ├── test_ingestion.py      # Test event POST endpoints
│   │   │   ├── test_analytics.py      # Test dashboard queries
│   │   │   └── test_auth.py           # Test JWT auth flow
│   │   ├── unit/
│   │   │   ├── test_demo_data_service.py  # Validate synthetic data distributions
│   │   │   └── test_analytics_service.py  # Validate metric calculations
│   │   └── conftest.py            # pytest fixtures (test DB, client)
│   ├── alembic/                   # Database migrations
│   │   ├── versions/              # Migration scripts
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── requirements.txt           # Backend Python dependencies
│   ├── Dockerfile                 # Backend container image
│   └── pyproject.toml             # Backend project metadata (optional)
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx               # React app entry point
│   │   ├── App.tsx                # Root component with routing
│   │   ├── components/            # Reusable UI components
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── charts/
│   │   │   │   ├── ComplianceTrendChart.tsx
│   │   │   │   ├── StepBarChart.tsx
│   │   │   │   └── TimingChart.tsx
│   │   │   ├── filters/
│   │   │   │   ├── DateRangeFilter.tsx
│   │   │   │   ├── UnitFilter.tsx
│   │   │   │   ├── ShiftFilter.tsx
│   │   │   │   └── QualityToggle.tsx
│   │   │   └── common/
│   │   │       ├── MetricCard.tsx
│   │   │       ├── DeviceStatusBadge.tsx
│   │   │       └── Loader.tsx
│   │   ├── pages/                 # Page-level components
│   │   │   ├── OverviewPage.tsx   # Org-wide dashboard
│   │   │   ├── UnitPage.tsx       # Unit drilldown
│   │   │   ├── DevicePage.tsx     # Device detail view
│   │   │   ├── LoginPage.tsx      # Authentication
│   │   │   └── NotFoundPage.tsx
│   │   ├── services/              # API client functions
│   │   │   ├── api.ts             # Axios instance with auth interceptor
│   │   │   ├── analyticsApi.ts    # Analytics endpoints
│   │   │   ├── devicesApi.ts      # Device endpoints
│   │   │   └── authApi.ts         # Auth endpoints
│   │   ├── hooks/                 # Custom React hooks
│   │   │   ├── useAnalytics.ts    # React Query hook for analytics
│   │   │   ├── useDevices.ts      # React Query hook for devices
│   │   │   ├── useAuth.ts         # Auth context hook
│   │   │   └── useFilters.ts      # Filter state management
│   │   ├── context/               # React context providers
│   │   │   ├── AuthContext.tsx    # Auth state provider
│   │   │   └── FilterContext.tsx  # Global filter state
│   │   ├── types/                 # TypeScript type definitions
│   │   │   ├── analytics.ts       # Analytics response types
│   │   │   ├── device.ts          # Device types
│   │   │   └── auth.ts            # Auth types
│   │   └── utils/                 # Utility functions
│   │       ├── dateUtils.ts       # Date formatting, range calculations
│   │       └── formatters.ts      # Number formatting, duration display
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── dateUtils.test.ts
│   │   │   └── formatters.test.ts
│   │   └── smoke/
│   │       └── dashboard.spec.ts  # Playwright smoke test
│   ├── public/                    # Static assets
│   ├── index.html                 # HTML entry point
│   ├── package.json               # Frontend dependencies
│   ├── tsconfig.json              # TypeScript config
│   ├── vite.config.ts             # Vite bundler config
│   ├── Dockerfile                 # Frontend container image
│   └── .env.example               # Environment variable template
│
└── docker-compose.yml             # Orchestrate db + backend + frontend

# Scripts for demo and development
scripts/
├── reset-demo.sh                  # Wipe DB + reseed synthetic data (one command)
└── start-dashboard.sh             # Start docker-compose stack

# Database
migrations/                         # SQL migration files (alternative to Alembic)
└── 001_initial_schema.sql         # Initial schema + materialized views

# Configuration
.env.example                        # Environment variables for docker-compose
```

**Structure Decision**: Selected **Option 2: Web application** structure with separate `dashboard/backend/` and `dashboard/frontend/` directories. This keeps dashboard code isolated from existing device detection code in `src/deltawash_pi/`, maintaining clear separation of concerns per constitution's modular architecture principle. Device code requires only minimal changes to logging layer for HTTP event posting.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Repository pattern (repositories/ layer) | Isolate SQLAlchemy queries from service logic; enable easier testing of analytics calculations without DB | Direct DB access in services acceptable for MVP; repository layer adds premature abstraction. **DECISION: Omit repositories/ for MVP; use SQLAlchemy queries directly in services. Can refactor later if query logic becomes complex.** |
| Adding 3rd component (dashboard) to device + ESP8266 system | Dashboard provides essential analytics for multi-device monitoring; spec explicitly requires demo data and org-wide dashboards | Cannot achieve org-wide analytics with per-device local logs alone; centralized storage required for aggregation across 20+ devices |
| PostgreSQL materialized views | Dashboard queries must return <200ms p95 for aggregated metrics; naive JOINs across 500+ sessions too slow | Real-time aggregation on every query fails performance constraint; pre-computed views required for <1s filter updates |
