# Feature Specification: Hospital Dashboard for Handwashing Compliance Analytics

**Feature Branch**: `002-hospital-dashboard`  
**Created**: January 10, 2026  
**Status**: Draft  
**Input**: User description: "Dashboard website for hospitals with many handwashing compliance systems for DeltaHacks demo"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Organization-Wide Compliance Overview (Priority: P1)

As an Org Admin or Analyst, I need to see aggregate compliance metrics across all devices and units to identify trends and problem areas at the organizational level.

**Why this priority**: This is the primary value proposition—providing executives and analysts with actionable insights across the entire organization. Without this view, the dashboard serves no purpose for decision-makers.

**Independent Test**: Can be fully tested by loading the dashboard with synthetic multi-device data and verifying that all overview metrics (compliance trend, most missed step, average times, quality rate, device status) display correctly and update when filters are applied.

**Acceptance Scenarios**:

1. **Given** synthetic data exists for 20+ devices across 7+ days with varied compliance, **When** user opens the overview dashboard, **Then** the system displays compliance trend chart, most missed step indicator, average wash time, average step times, quality rate percentage, and device last-seen summary
2. **Given** the overview dashboard is loaded, **When** user applies date range filter (e.g., last 3 days), **Then** all metrics recalculate to show only data within the selected range
3. **Given** the overview dashboard is loaded, **When** user applies unit filter, **Then** all metrics recalculate to show only data from selected unit(s)
4. **Given** the overview dashboard is loaded, **When** user applies shift/time-of-day filter (e.g., morning shift 7am-3pm), **Then** all metrics recalculate to show only sessions within selected time buckets
5. **Given** the overview dashboard is loaded, **When** user toggles "exclude low-quality sessions", **Then** all metrics recalculate excluding sessions flagged as low quality

---

### User Story 2 - Drill Down into Unit Performance (Priority: P2)

As a Unit Manager, I need to see compliance metrics scoped to my specific unit and compare devices within my unit to identify which devices need attention.

**Why this priority**: Unit managers need localized insights to manage their teams effectively. This enables decentralized accountability and action.

**Independent Test**: Can be fully tested by selecting a specific unit and verifying that metrics are filtered to that unit, and the device leaderboard shows devices ranked by relevant metrics (e.g., compliance rate, uptime).

**Acceptance Scenarios**:

1. **Given** synthetic data exists for multiple units, **When** user selects a specific unit, **Then** the system displays unit-scoped compliance trend, most missed step, average times, and quality rate
2. **Given** unit drilldown view is active, **When** user views the device leaderboard, **Then** the system displays devices ranked by compliance rate with visual indicators (e.g., top 3 green, bottom 3 red)
3. **Given** unit drilldown view is active, **When** user applies date range filter, **Then** unit metrics and leaderboard update to reflect only the selected date range
4. **Given** unit drilldown view is active, **When** user applies shift filter, **Then** unit metrics and leaderboard update to reflect only sessions from selected shift

---

### User Story 3 - Monitor Individual Device Health (Priority: P2)

As a Technician, I need to view the operational status and reliability of individual devices to prioritize maintenance and troubleshoot connectivity issues.

**Why this priority**: Ensures devices remain operational and data collection is reliable. Critical for maintaining data quality.

**Independent Test**: Can be fully tested by viewing device detail page and verifying display of last-seen timestamp, heartbeat status, version info, and reliability flags (e.g., offline periods, connectivity issues).

**Acceptance Scenarios**:

1. **Given** a device has reported heartbeat events, **When** user views the device detail page, **Then** the system displays last-seen timestamp, heartbeat frequency metrics, firmware/software version, and online/offline status
2. **Given** a device has been offline for extended periods, **When** user views the device detail page, **Then** the system displays reliability flags indicating offline periods and time since last activity
3. **Given** multiple devices exist, **When** user views the overview dashboard, **Then** the system displays a summary of device statuses (e.g., "18/20 devices online, 2 offline")

---

### User Story 4 - Load Demo Data for Multi-Device Simulation (Priority: P1)

As a demo presenter (Org Admin), I need to populate the system with realistic synthetic data representing multiple hospitals/units, many devices, and days of activity to demonstrate analytics capabilities when only one physical device exists.

**Why this priority**: Critical for DeltaHacks demo success. Without synthetic data generation, we cannot demonstrate multi-device analytics with only one physical device.

**Independent Test**: Can be fully tested by triggering demo data generation (via button, CLI, or file upload) and verifying that the database contains at least 20 devices, 7 days of data, 500+ sessions with realistic variation (missed steps, timing distributions, quality flags, offline periods).

**Acceptance Scenarios**:

1. **Given** the system is empty or has minimal data, **When** user triggers "Generate Demo Dataset" action, **Then** the system populates the database with synthetic data for at least 20 devices, 7 days, 500+ sessions including variation in compliance, step timing, quality flags, and device offline periods
2. **Given** the system supports file upload, **When** user uploads a CSV/JSON file with session records, **Then** the system ingests the data and makes it available for dashboard analytics
3. **Given** demo data has been generated, **When** user views overview dashboard, **Then** the system displays analytics computed from both live device data (if any) and synthetic demo data
4. **Given** demo data includes device offline periods, **When** user views device health metrics, **Then** the system accurately reflects offline/online status and gaps in data

---

### User Story 5 - Receive Live Device Events (Priority: P2)

As the system, I need to accept session events, step events, and heartbeat events via HTTP from physical handwashing compliance devices to provide real-time analytics.

**Why this priority**: Enables integration with actual devices. Lower priority than demo data for DeltaHacks but essential for production use.

**Independent Test**: Can be fully tested by sending HTTP POST requests with session, step, and heartbeat payloads to the ingestion endpoint and verifying that data is stored and reflected in dashboard metrics.

**Acceptance Scenarios**:

1. **Given** a device completes a handwashing session, **When** the device sends a session event via HTTP POST, **Then** the system stores the session data and updates compliance metrics
2. **Given** a device completes a handwashing step, **When** the device sends a step event via HTTP POST, **Then** the system stores the step data and updates step-level metrics
3. **Given** a device sends periodic heartbeat events, **When** the device POSTs heartbeat data, **Then** the system updates device last-seen timestamp and online status
4. **Given** a device event is received, **When** the event contains invalid or malformed data, **Then** the system rejects the event and logs an error without crashing

---

### Edge Cases

- What happens when a device reports sessions with missing steps? (System should count these as non-compliant and flag them in "most missed step" analysis)
- What happens when no data exists for a selected filter combination (e.g., unit X on date Y)? (System should display empty state with message "No data available for selected filters")
- What happens when synthetic data generation is triggered multiple times? (System should either append new synthetic data with different device IDs or clear existing synthetic data before regenerating—must be deterministic)
- What happens when a device has not sent a heartbeat for an extended period (e.g., >24 hours)? (System should flag device as offline and display warning in device status summary)
- What happens when a user applies conflicting filters (e.g., date range with no data for selected unit)? (System should display appropriate message and allow user to adjust filters)
- What happens when synthetic data contains unrealistic values (e.g., wash time of 5 seconds)? (System should apply validation rules and either reject or flag suspicious data)
- What happens when the dashboard is accessed on mobile devices? (System should provide responsive layout—specific mobile requirements may need clarification based on target user context)

## Requirements *(mandatory)*

### Functional Requirements

#### Data Ingestion

- **FR-001**: System MUST accept session event data via HTTP POST endpoint including device ID, timestamp, duration, steps completed, steps missed, quality flag, and unit identifier
- **FR-002**: System MUST accept step event data via HTTP POST endpoint including device ID, step ID, timestamp, duration, and quality metrics
- **FR-003**: System MUST accept heartbeat event data via HTTP POST endpoint including device ID, timestamp, firmware version, and online status
- **FR-004**: System MUST provide at least one method for demo data ingestion: either a "Generate Demo Dataset" UI button, a CLI command, file upload interface, or scheduled generator
- **FR-005**: System MUST generate synthetic demo data containing at least 20 devices, 7 days of historical data, and 500+ sessions when demo generation is triggered
- **FR-006**: Synthetic demo data MUST include realistic variation: missed steps (5-20% non-compliance rate), timing distributions (step durations varying by ±30% from mean), quality flags (10-15% low-quality sessions), and device offline periods (5-10% downtime per device)
- **FR-007**: Synthetic demo data MUST include multiple units (at least 3 units) or multiple hospitals, with devices distributed across units

#### Dashboard Views

- **FR-008**: System MUST provide an Overview Dashboard displaying: compliance trend over time (chart), most frequently missed step, average wash time, average time per step type, quality rate percentage, and device last-seen summary
- **FR-009**: System MUST provide a Unit Drilldown View displaying: unit-scoped compliance trend, most missed step for unit, average times for unit, quality rate for unit, and device leaderboard ranking devices by compliance rate
- **FR-010**: System MUST provide a Device View for each device displaying: last-seen timestamp, heartbeat frequency, firmware/software version, online/offline status, and reliability flags (e.g., offline periods, connectivity warnings)

#### Filtering and Interaction

- **FR-011**: System MUST support date range filtering on all dashboard views with at least the following preset ranges: last 24 hours, last 7 days, last 30 days, custom range
- **FR-012**: System MUST support unit/device filtering allowing users to select specific units or devices to scope analytics
- **FR-013**: System MUST support shift/time-of-day filtering with configurable time buckets (e.g., morning: 7am-3pm, afternoon: 3pm-11pm, night: 11pm-7am)
- **FR-014**: System MUST provide an "exclude low-quality sessions" toggle that filters out sessions flagged as low-quality from all metrics
- **FR-015**: System MUST apply filters consistently across all metrics within a dashboard view and update metrics dynamically when filters change

#### Data Quality and Validation

- **FR-016**: System MUST validate incoming device events for required fields and reject malformed events with appropriate error responses
- **FR-017**: System MUST flag sessions as low-quality when quality metrics fall below configurable thresholds (e.g., poor hand detection, insufficient coverage)
- **FR-018**: System MUST log all device events (session, step, heartbeat) with timestamps for audit and debugging purposes

#### User Access and Personas

- **FR-019**: System MUST support the following user personas with appropriate access levels: Org Admin (full access), Analyst (read-only access to all views), Unit Manager (access to own unit's data), Technician (access to device health views)
- **FR-020**: System MUST present appropriate default views based on user persona (e.g., Org Admin sees overview, Unit Manager sees unit drilldown, Technician sees device list)

### Key Entities

- **Device**: Represents a physical handwashing compliance system; attributes include unique device ID, unit assignment, firmware version, installation date, last-seen timestamp, online/offline status
- **Unit**: Represents a physical location or organizational division (e.g., ICU, ER, Surgery); attributes include unique unit ID, hospital identifier, unit name
- **Session**: Represents a single handwashing event; attributes include unique session ID, device ID, start timestamp, end timestamp, duration, steps completed, steps missed, quality flag, overall compliance status
- **Step**: Represents a specific handwashing step within a session; attributes include step ID (e.g., step2, step3, step4), session ID, duration, quality metrics, detection confidence
- **Heartbeat**: Represents a device health check event; attributes include device ID, timestamp, firmware version, connectivity status
- **User**: Represents a dashboard user; attributes include user ID, persona type (Org Admin, Analyst, Unit Manager, Technician), unit assignment (for Unit Managers), authentication credentials

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Demo presenters can generate a complete synthetic dataset (20+ devices, 7+ days, 500+ sessions) in under 30 seconds
- **SC-002**: Dashboard displays analytics for 20+ devices and 500+ sessions with page load times under 3 seconds and filter updates under 1 second
- **SC-003**: System correctly computes compliance trends, most missed steps, and average times with 100% accuracy when validated against known synthetic data
- **SC-004**: Unit Managers can identify their lowest-performing devices within 10 seconds of viewing the unit drilldown page
- **SC-005**: Technicians can identify offline devices within 5 seconds of viewing the overview dashboard
- **SC-006**: System successfully ingests and displays live device events within 5 seconds of event receipt (batch processing acceptable for MVP)
- **SC-007**: All dashboard views remain functional and accurate when filtering by any combination of date range, unit, shift, and quality flags
- **SC-008**: Demo presenters can successfully demonstrate multi-device analytics capabilities at DeltaHacks using only one physical device supplemented with synthetic data
- **SC-009**: 100% of malformed device events are rejected with appropriate error messages and do not corrupt analytics data
- **SC-010**: System supports at least 4 concurrent dashboard users without performance degradation (sufficient for DeltaHacks demo)

## Assumptions

- Users access the dashboard via desktop or tablet browsers (Chrome, Firefox, Safari); mobile phone support is not required for DeltaHacks MVP
- Users have reliable network connectivity; offline mode is not required
- Synthetic data generation uses randomization with realistic constraints (not ML-generated); manual tuning of distribution parameters is acceptable
- Session data from the physical device follows the same schema as synthetic data
- User authentication is simplified for MVP (e.g., basic auth or single admin account); full role-based access control with user management can be deferred
- Database can reside on a single instance; distributed database architecture is not required for MVP scale (20 devices, ~1000 sessions/day)
- Historical data retention is unlimited for MVP; data archival and deletion policies can be defined later
- Heartbeat frequency is configurable per device (default: every 5 minutes); exact interval will be determined during implementation
- Shift time buckets are configurable system-wide (not per-hospital or per-unit) for MVP
- Quality flags are binary (low-quality vs normal) for MVP; granular quality scores can be added later
- Device firmware version is reported by the device; version compatibility checks are out of scope for MVP
- Hospitals and units are pre-configured; dynamic hospital/unit registration is not required for DeltaHacks

## Out of Scope

- **Video Storage**: System does not store handwashing session videos; only metadata and step completion data are persisted
- **Staff Identity Tracking**: System does not identify individual staff members performing handwashing; no surveillance or individual performance tracking features
- **Real-Time Guarantees**: System does not guarantee real-time data processing; batch processing with up to 5-second latency is acceptable for MVP
- **Alerting and Notifications**: System does not send alerts or notifications for compliance issues or device failures (future enhancement)
- **Custom Reporting**: System does not support custom report generation or data export (future enhancement)
- **Multi-Tenancy**: System does not enforce strict data isolation between hospitals; access control is simplified for MVP
- **Advanced Analytics**: Machine learning-based predictions, anomaly detection, and forecasting are out of scope
- **Mobile Applications**: Native mobile apps (iOS/Android) are out of scope; responsive web design for tablets is sufficient
- **Internationalization**: Multi-language support and localization are out of scope
- **Audit Logging for User Actions**: System logs device events but not user dashboard interactions (future enhancement)
