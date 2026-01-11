# API Contracts: Hospital Dashboard

**Feature**: Hospital Dashboard for Handwashing Compliance Analytics  
**Created**: January 10, 2026  
**Purpose**: Define HTTP endpoint contracts (request/response schemas, status codes, error handling)

## Base URL

**Development**: `http://localhost:8000/api/v1`  
**Production**: `https://{domain}/api/v1`

## Authentication

All endpoints except `/auth/login` require JWT authentication.

**Header**: `Authorization: Bearer <jwt_token>`

**Token Claims**:
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "org_admin|analyst|unit_manager|technician",
  "unit_id": "uuid or null",
  "exp": 1234567890
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Invalid or expired token"
}
```

---

## Endpoints

### Authentication

#### POST `/auth/login`

**Purpose**: Authenticate user and receive JWT token

**Request**:
```json
{
  "email": "admin@hospital.com",
  "password": "securepassword"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "a1b2c3d4-...",
    "email": "admin@hospital.com",
    "role": "org_admin",
    "unit_id": null
  }
}
```

**Errors**:
- 400 Bad Request: Invalid email format
- 401 Unauthorized: Incorrect email or password
- 422 Unprocessable Entity: Missing required fields

---

### Event Ingestion

#### POST `/events/session`

**Purpose**: Accept session event from device

**Authorization**: Requires `device` role (separate token for devices)

**Request**:
```json
{
  "device_id": "device-uuid",
  "timestamp": "2026-01-10T14:30:00Z",
  "duration_ms": 32500,
  "compliant": true,
  "missed_steps": [],
  "low_quality": false,
  "config_version": "abc123def456"
}
```

**Response** (201 Created):
```json
{
  "session_id": "session-uuid",
  "message": "Session recorded successfully"
}
```

**Errors**:
- 400 Bad Request: Invalid device_id or timestamp format
- 422 Unprocessable Entity: duration_ms out of range (5000-120000)
- 500 Internal Server Error: Database insertion failed

---

#### POST `/events/step`

**Purpose**: Accept step event from device

**Authorization**: Requires `device` role

**Request**:
```json
{
  "session_id": "session-uuid",
  "step_id": 3,
  "duration_ms": 8500,
  "completed": true,
  "confidence_score": 0.92
}
```

**Response** (201 Created):
```json
{
  "step_id": "step-record-uuid",
  "message": "Step recorded successfully"
}
```

**Errors**:
- 400 Bad Request: Invalid session_id or step_id out of range [2-7]
- 404 Not Found: Session not found
- 422 Unprocessable Entity: confidence_score out of range [0.0-1.0]

---

#### POST `/events/heartbeat`

**Purpose**: Accept heartbeat event from device

**Authorization**: Requires `device` role

**Request**:
```json
{
  "device_id": "device-uuid",
  "timestamp": "2026-01-10T14:35:00Z",
  "firmware_version": "v1.2.3",
  "online_status": true
}
```

**Response** (201 Created):
```json
{
  "heartbeat_id": "heartbeat-uuid",
  "message": "Heartbeat recorded successfully"
}
```

**Errors**:
- 400 Bad Request: Invalid device_id or timestamp in future
- 422 Unprocessable Entity: Invalid firmware_version format

---

### Analytics

#### GET `/analytics/overview`

**Purpose**: Get organization-wide analytics dashboard data

**Authorization**: Requires `org_admin` or `analyst` role

**Query Parameters**:
- `date_from` (string, ISO 8601 date, required): Start of date range
- `date_to` (string, ISO 8601 date, required): End of date range
- `unit_id` (string, UUID, optional): Filter by specific unit
- `shift` (string, enum, optional): Filter by shift (`morning`, `afternoon`, `night`)
- `exclude_low_quality` (boolean, optional, default: false): Exclude low-quality sessions

**Example Request**:
```
GET /analytics/overview?date_from=2026-01-10&date_to=2026-01-10&exclude_low_quality=true
```

**Response** (200 OK):
```json
{
  "compliance_trend": [
    {
      "date": "2026-01-10",
      "total_sessions": 142,
      "compliant_sessions": 128,
      "compliance_rate": 90.14
    },
    {
      "date": "2026-01-10",
      "total_sessions": 138,
      "compliant_sessions": 125,
      "compliance_rate": 90.58
    }
  ],
  "most_missed_step": {
    "step_id": 5,
    "step_name": "Backs of fingers to opposing palms",
    "miss_count": 156,
    "miss_rate": 11.2
  },
  "average_wash_time_ms": 31250,
  "average_step_times": [
    {"step_id": 2, "avg_duration_ms": 6500},
    {"step_id": 3, "avg_duration_ms": 9200},
    {"step_id": 4, "avg_duration_ms": 7800},
    {"step_id": 5, "avg_duration_ms": 5900},
    {"step_id": 6, "avg_duration_ms": 6100},
    {"step_id": 7, "avg_duration_ms": 5750}
  ],
  "quality_rate": 88.5,
  "device_summary": {
    "total_devices": 20,
    "online_devices": 18,
    "offline_devices": 2
  },
  "metadata": {
    "date_from": "2026-01-10",
    "date_to": "2026-01-10",
    "filters_applied": {
      "exclude_low_quality": true
    },
    "last_refreshed": "2026-01-10T14:30:00Z"
  }
}
```

**Errors**:
- 400 Bad Request: Invalid date format or date_from > date_to
- 403 Forbidden: User role not authorized (e.g., technician attempting access)
- 422 Unprocessable Entity: Missing required parameters

---

#### GET `/analytics/unit/{unit_id}`

**Purpose**: Get unit-scoped analytics dashboard data

**Authorization**: Requires `org_admin`, `analyst`, or `unit_manager` with matching `unit_id`

**Path Parameters**:
- `unit_id` (string, UUID, required): Unit identifier

**Query Parameters**: Same as `/analytics/overview` except `unit_id` (already in path)

**Response** (200 OK):
```json
{
  "unit": {
    "id": "unit-uuid",
    "name": "Intensive Care Unit",
    "code": "ICU"
  },
  "compliance_trend": [
    {"date": "2026-01-10", "total_sessions": 28, "compliant_sessions": 26, "compliance_rate": 92.86}
  ],
  "most_missed_step": {
    "step_id": 6,
    "step_name": "Rotational rubbing of thumbs",
    "miss_count": 12,
    "miss_rate": 8.5
  },
  "average_wash_time_ms": 30200,
  "average_step_times": [...],
  "quality_rate": 91.2,
  "device_leaderboard": [
    {
      "device_id": "device-uuid-1",
      "device_name": "ICU-Device-01",
      "total_sessions": 72,
      "compliant_sessions": 69,
      "compliance_rate": 95.83,
      "rank": 1
    },
    {
      "device_id": "device-uuid-2",
      "device_name": "ICU-Device-02",
      "total_sessions": 68,
      "compliant_sessions": 62,
      "compliance_rate": 91.18,
      "rank": 2
    }
  ],
  "metadata": {
    "date_from": "2026-01-10",
    "date_to": "2026-01-10",
    "last_refreshed": "2026-01-10T14:30:00Z"
  }
}
```

**Errors**:
- 403 Forbidden: unit_manager attempting to access different unit
- 404 Not Found: Unit not found

---

#### GET `/analytics/device/{device_id}`

**Purpose**: Get device health and performance metrics

**Authorization**: Requires any authenticated role

**Path Parameters**:
- `device_id` (string, UUID, required): Device identifier

**Query Parameters**: Same as `/analytics/overview` (for scoping metrics to date range)

**Response** (200 OK):
```json
{
  "device": {
    "id": "device-uuid",
    "name": "ICU-Device-01",
    "unit_id": "unit-uuid",
    "unit_name": "Intensive Care Unit",
    "firmware_version": "v1.2.3",
    "installation_date": "2026-01-10T10:00:00Z"
  },
  "status": {
    "last_seen": "2026-01-10T14:30:00Z",
    "is_online": true,
    "heartbeats_24h": 288,
    "expected_heartbeats_24h": 288,
    "uptime_percentage": 100.0
  },
  "performance": {
    "total_sessions": 72,
    "compliant_sessions": 69,
    "compliance_rate": 95.83,
    "average_wash_time_ms": 30500,
    "average_quality_score": 92.5
  },
  "reliability_flags": [],
  "metadata": {
    "date_from": "2026-01-10",
    "date_to": "2026-01-10",
    "last_refreshed": "2026-01-10T14:30:00Z"
  }
}
```

**Reliability Flags** (examples):
```json
"reliability_flags": [
  {
    "type": "offline_period",
    "severity": "warning",
    "message": "Device was offline from 2026-01-10 08:00 to 2026-01-10 12:30 (4.5 hours)",
    "timestamp": "2026-01-10T08:00:00Z"
  },
  {
    "type": "low_heartbeat_rate",
    "severity": "info",
    "message": "Heartbeat rate dropped to 80% of expected on 2026-01-10",
    "timestamp": "2026-01-10T00:00:00Z"
  }
]
```

**Errors**:
- 404 Not Found: Device not found

---

### Devices

#### GET `/devices`

**Purpose**: List all devices with optional filtering

**Authorization**: Requires any authenticated role

**Query Parameters**:
- `unit_id` (string, UUID, optional): Filter by unit
- `online_only` (boolean, optional, default: false): Show only online devices

**Response** (200 OK):
```json
{
  "devices": [
    {
      "id": "device-uuid-1",
      "name": "ICU-Device-01",
      "unit_id": "unit-uuid",
      "unit_name": "Intensive Care Unit",
      "firmware_version": "v1.2.3",
      "last_seen": "2026-01-10T14:30:00Z",
      "is_online": true
    },
    {
      "id": "device-uuid-2",
      "name": "ER-Device-05",
      "unit_id": "unit-uuid-2",
      "unit_name": "Emergency Room",
      "firmware_version": "v1.2.3",
      "last_seen": "2026-01-10T12:15:00Z",
      "is_online": false
    }
  ],
  "total_count": 20,
  "online_count": 18,
  "offline_count": 2
}
```

---

#### GET `/devices/{device_id}`

**Purpose**: Get detailed device information

**Authorization**: Requires any authenticated role

**Response** (200 OK):
```json
{
  "id": "device-uuid",
  "name": "ICU-Device-01",
  "unit_id": "unit-uuid",
  "unit_name": "Intensive Care Unit",
  "firmware_version": "v1.2.3",
  "installation_date": "2026-01-10T10:00:00Z",
  "last_seen": "2026-01-10T14:30:00Z",
  "is_online": true,
  "created_at": "2026-01-10T10:00:00Z",
  "updated_at": "2026-01-10T14:30:00Z"
}
```

**Errors**:
- 404 Not Found: Device not found

---

### Administration

#### POST `/admin/refresh-aggregates`

**Purpose**: Manually trigger materialized view refresh

**Authorization**: Requires `org_admin` role

**Request**: No body required

**Response** (200 OK):
```json
{
  "message": "Materialized views refreshed successfully",
  "views_refreshed": [
    "mv_daily_compliance",
    "mv_step_statistics",
    "mv_device_status"
  ],
  "refresh_duration_ms": 1250,
  "refreshed_at": "2026-01-10T14:35:00Z"
}
```

**Errors**:
- 403 Forbidden: User role not authorized
- 500 Internal Server Error: Refresh failed

---

#### POST `/admin/demo-data/generate`

**Purpose**: Generate synthetic demo data (alternative to CLI)

**Authorization**: Requires `org_admin` role

**Request**:
```json
{
  "devices": 20,
  "days": 7,
  "sessions_per_day": 10,
  "miss_rate": 0.15,
  "low_quality_rate": 0.12,
  "offline_rate": 0.08,
  "seed": 42
}
```

**Response** (201 Created):
```json
{
  "message": "Demo data generated successfully",
  "summary": {
    "units_created": 4,
    "devices_created": 20,
    "sessions_created": 1456,
    "steps_created": 8736,
    "heartbeats_created": 40320,
    "date_range": {
      "from": "2026-01-10",
      "to": "2026-01-10"
    }
  },
  "generation_duration_ms": 12500,
  "seed_used": 42
}
```

**Errors**:
- 403 Forbidden: User role not authorized
- 422 Unprocessable Entity: Invalid parameters (e.g., devices < 1, days < 1)

---

#### DELETE `/admin/demo-data/wipe`

**Purpose**: Wipe all data (for demo reset)

**Authorization**: Requires `org_admin` role

**Request**: No body required

**Response** (200 OK):
```json
{
  "message": "All data wiped successfully",
  "records_deleted": {
    "sessions": 1456,
    "steps": 8736,
    "heartbeats": 40320,
    "devices": 20,
    "units": 4
  }
}
```

**Errors**:
- 403 Forbidden: User role not authorized

---

## Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE_CONSTANT",
  "timestamp": "2026-01-10T14:30:00Z",
  "path": "/api/v1/analytics/overview",
  "request_id": "req-uuid"
}
```

**Common Error Codes**:
- `INVALID_TOKEN`: JWT token invalid or expired
- `INSUFFICIENT_PERMISSIONS`: User role lacks required permission
- `RESOURCE_NOT_FOUND`: Requested resource (device, unit, session) not found
- `VALIDATION_ERROR`: Request payload validation failed
- `DATABASE_ERROR`: Internal database error

---

## Rate Limiting

**MVP**: No rate limiting enforced

**Future**: 
- 100 requests/minute per user for analytics endpoints
- 1000 requests/minute per device for ingestion endpoints

---

## Versioning

**Current Version**: v1

**Breaking Changes**: Will introduce v2 with deprecation notice

**Deprecation Policy**:
- 6 months notice before removing v1 endpoints
- Deprecation headers in v1 responses: `X-API-Deprecated: true`

---

## CORS Configuration

**Development**: Allow `http://localhost:5173` (Vite dev server)

**Production**: Restrict to dashboard domain only

**Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS

**Allowed Headers**: `Authorization`, `Content-Type`

---

## Pagination

**Not Implemented in MVP** (all queries return full result sets)

**Future**: 
- Add `page` and `page_size` query parameters
- Return `pagination` metadata in responses:
  ```json
  {
    "data": [...],
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total_pages": 10,
      "total_items": 500
    }
  }
  ```

---

## OpenAPI Schema

**Available at**: `GET /docs` (Swagger UI)

**JSON Schema**: `GET /openapi.json`

FastAPI automatically generates OpenAPI schema from Pydantic models and route definitions.
