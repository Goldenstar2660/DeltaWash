# Data Model: WHO Steps 2-7 Compliance

## Entities

### SessionRecord
| Field | Type | Description |
| --- | --- | --- |
| `session_id` | string (UUID) | Unique identifier per washing attempt. |
| `config_version` | string | Hash or semantic version of the active config profile. |
| `model_version` | optional string | Hash or version of the loaded model file (null when heuristic-only). |
| `start_ts` | ISO-8601 timestamp | Session start time. |
| `end_ts` | ISO-8601 timestamp | Session end time (nullable until closed). |
| `roi_rect` | object `{x, y, width, height}` | ROI coordinates captured from the active config (no separate calibration profile). |
| `demo_mode` | bool | True when replaying deterministic demo assets. |
| `demo_asset_id` | optional string | Asset identifier recorded when `demo_mode=true` (consumed by the accuracy CLI). |
| `step_statuses` | array<StepStatus> | Snapshot of every step at session close. |
| `uncertainty_events` | array<UncertaintyEvent> | Logged ambiguity/confidence drops. |
| `fallback_events` | array<FallbackEvent> | Logged heuristic/model fallback occurrences. |
| `total_rubbing_ms` | int | Sum of accumulated time across all steps. |
| `model_inference_count` | int | Number of model inferences performed. |
| `heuristic_fallback_count` | int | Number of times heuristics or demo annotations substituted for the ML model. |
| `avg_inference_time_ms` | optional float | Mean model inference latency (ms) across inferences. |
| `inference_time_samples` | int | Count of inference latency samples included in the average. |
| `inference_time_sum_ms` | float | Raw sum of inference latency samples for aggregate recomputation. |
| `avg_model_confidence` | optional float | Mean model confidence for the session. |
| `model_confidence_samples` | int | Number of confidence samples collected. |
| `model_confidence_sum` | float | Raw sum of confidence values (used by aggregations). |
| `model_usage_rate` | float | Percentage of classifications emitted by the ML model vs. fallback signals. |
| `notes` | array<string> | Free-form observations (duration, stop reason, capture warnings, etc.). |

### StepStatus
| Field | Type | Description |
| --- | --- | --- |
| `step_id` | enum(`STEP_2`..`STEP_7`) | Canonical WHO step. |
| `orientation` | enum(...) | Populated for steps with variants. |
| `state` | enum(`NOT_STARTED`,`IN_PROGRESS`,`COMPLETED`,`UNCERTAIN`) | Final state at session end. |
| `accumulated_ms` | int | Confident dwell time. |
| `completed_ts` | optional timestamp | Time when completion threshold met. |
| `uncertainty_count` | int | Number of uncertainty intervals impacting this step. |
| `classification_source` | enum(`MODEL`,`HEURISTIC`,`MIXED`,`UNKNOWN`) | Whether the ML model, heuristic/demo fallbacks, or both contributed. |
| `model_confidence_avg` | optional float | Average model confidence when the source includes MODEL. |

### ModelInferenceResult
| Field | Type | Description |
| --- | --- | --- |
| `step_id` | enum(`STEP_2`..`STEP_7`, `NONE`) | Predicted WHO step from model. |
| `confidence` | float [0,1] | Model output confidence (softmax probability). |
| `orientation` | enum(...) | Orientation variant if applicable. |
| `inference_time_ms` | float | Time taken for model inference. |
| `window_start_ts` | int | Timestamp of first frame in the landmark window. |
| `window_end_ts` | int | Timestamp of last frame in the landmark window. |
| `model_version` | string | Version/hash of the model file used. |

### LandmarkWindow
| Field | Type | Description |
| --- | --- | --- |
| `window_id` | int | Sequence number of the window within session. |
| `frame_count` | int | Number of frames in the window (typically 16-24). |
| `start_ts` | int | Timestamp of first frame in window. |
| `end_ts` | int | Timestamp of last frame in window. |
| `landmarks` | array | Normalized landmark array [frames × hands × 21 × 3]. |
| `hand_count_per_frame` | array<int> | Number of hands detected per frame. |
| `avg_landmark_confidence` | float | Mean MediaPipe confidence across window. |

### UncertaintyEvent
| Field | Type | Description |
| --- | --- | --- |
| `timestamp_ms` | int | When the event occurred. |
| `reason` | enum(`AMBIGUOUS_HANDS`,`LOW_CONFIDENCE`,`CAMERA_DROPPED`,`ROI_EXIT`) | Categorical reason. |
| `details` | string | Optional diagnostics. |

### FallbackEvent
| Field | Type | Description |
| --- | --- | --- |
| `timestamp_ms` | int | When fallback occurred. |
| `reason` | enum(`MODEL_MISSING`,`MODEL_INVALID`,`LANDMARK_LOW_CONFIDENCE`,`MODEL_LOW_CONFIDENCE`,`WINDOW_INCOMPLETE`) | Why heuristic fallback was used. |
| `model_confidence` | optional float | Model confidence if applicable. |
| `landmark_confidence` | optional float | MediaPipe confidence if applicable. |
| `heuristic_result` | optional string | Step ID returned by heuristic fallback. |

### AggregateStats
| Field | Type | Description |
| --- | --- | --- |
| `stats_version` | string | Version/hash of aggregation logic. |
| `generated_ts` | timestamp | When aggregates computed. |
| `sessions_count` | int | Number of sessions included. |
| `most_missed_step` | enum | Step with highest incompletion rate. |
| `average_step_times_ms` | map | Mean accumulated_ms per step. |
| `uncertainty_frequency` | map | Count per UncertaintyEvent reason. |
| `fallback_frequency` | map | Count per FallbackEvent reason. |
| `model_usage_rate` | float | Percentage of classifications from ML model vs heuristics. |
| `avg_model_confidence` | float | Mean model confidence across all model-based classifications. |
| `avg_inference_time_ms` | float | Mean model inference latency across sessions. |
| `failure_patterns` | array<string> | Derived insights (e.g., "Step_6 low confidence"). |
| `accuracy` | optional AccuracySection | Accuracy evaluation results merged by the analytics CLI. |

### AccuracySection
| Field | Type | Description |
| --- | --- | --- |
| `generated_ts` | timestamp | When the accuracy report was produced. |
| `threshold` | float | Minimum acceptable completion accuracy (e.g., 0.85 for SC-001). |
| `value` | optional float | Observed accuracy across demo-mode sessions (null when insufficient data). |
| `status` | enum(`pass`,`fail`) | Comparison of `value` vs `threshold`. |
| `sessions_evaluated` | int | Number of demo-mode sessions included. |
| `steps_correct` | int | Count of correctly completed, orientation-matched steps. |
| `steps_expected` | int | Total annotated steps drawn from the manifest subset. |
| `assets` | map<asset_id, {`sessions`: int, `accuracy`: optional float}> | Per-asset drill-down used for debugging failing submissions. |

### LedSignal
| Field | Type | Description |
| --- | --- | --- |
| `step` | int | Numeric WHO step (2-7) for firmware that expects digits. |
| `step_id` | enum | Step identifier string (`STEP_2`..`STEP_7`). |
| `state` | enum(`CURRENT`,`COMPLETED`,`IDLE`) | LED presentation state. |
| `timestamp_ms` | int | When the interpreter emitted the event. |
| `blink_hz` | float | Blink cadence requested for CURRENT-state LEDs. |
| `delivered` | bool | Whether ESP8266 acknowledged. |
| `error` | optional string | Logged if delivery failed (client auto-disables on first error). |

### VideoCaptureArtifact
| Field | Type | Description |
| --- | --- | --- |
| `session_id` | string (UUID) | Session associated with the capture. |
| `storage_path` | string | Absolute path or prefix for stored files. |
| `start_ts` | ISO-8601 timestamp | Capture start time. |
| `end_ts` | ISO-8601 timestamp | Capture end time. |
| `retention_policy` | string | Policy used (e.g., `retention_seconds` or `max_sessions`). |

## Storage
- **Per-session logs**: JSON Lines file (`logs/sessions/<date>.jsonl`) with serialized `SessionRecord` objects.
- **Aggregates**: JSON file (`logs/aggregates/summary.json`) overwritten after each aggregation run.
- **Config profiles**: YAML or JSON under `config/` with schema described in contracts.

## Relationships
- Each `SessionRecord` references exactly one `ConfigProfile` via `config_version` hash.
- `AggregateStats` consumes many `SessionRecord` entries; regenerate when new sessions appended.
- `LedSignal` entries may be derived from `step_state_update` events and stored separately for validation.
