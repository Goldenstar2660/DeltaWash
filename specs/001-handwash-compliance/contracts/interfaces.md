# Interface Contracts

## Detector Module Interface

| Item | Description |
| --- | --- |
| Purpose | Standardize signals emitted by each WHO step detector module (Steps 2-7). |
| Input | `FramePacket` containing timestamp, frame_id, ROI metadata, MediaPipe landmarks, motion metrics, and config hash. |
| Output | `StepSignal` (defined below). |
| Invocation | Interpreter pulls each detector once per frame (or equivalent cadence); push/callback models are out of MVP scope. |
| Error Handling | Must return `is_confident=false` with a `notes` reason (e.g., `ambiguous_hands`, `invalid_landmarks`) or raise a structured error when landmarks are invalid; never crash interpreter thread. |

### StepSignal Structure

| Field | Type | Notes |
| --- | --- | --- |
| `step_id` | enum(`STEP_2`..`STEP_7`, `NONE`) | Canonical WHO step identifier. |
| `orientation` | enum(`NONE`,`RIGHT_OVER_LEFT`,`LEFT_OVER_RIGHT`,`LEFT_THUMB`,`RIGHT_THUMB`,`LEFT_FINGERTIPS`,`RIGHT_FINGERTIPS`) | Only used for steps 3, 6, 7. |
| `confidence` | float [0,1] | Classification confidence for this frame/window. |
| `is_confident` | bool | True if `confidence >= threshold` configured for this detector. |
| `source` | enum(`MODEL`,`HEURISTIC`,`DEMO`) | Whether classification came from the ML model, heuristic fallback, or demo annotations. |
| `timestamp_ms` | int | Source frame timestamp in ms. |
| `notes` | optional string | Diagnostic tag (`ambiguous_hands`, `demo_annotation`, `model_low_confidence`, etc.). |

## LandmarkSequenceClassifier Interface

| Item | Description |
| --- | --- |
| Purpose | Load a pre-trained model and classify WHO steps from temporal landmark sequences. |
| Input | `LandmarkWindow` containing normalized landmarks for ~16-24 frames (~0.5-1.0 s). |
| Output | `ModelInferenceResult` (defined below). |
| Initialization | Load model file at startup; validate format, input/output shapes, and version metadata. |
| Invocation | Called by `DetectorRunner` when model is available and landmark window is complete. |
| Error Handling | Return `step_id=NONE` with low confidence on inference errors; never crash the pipeline. |

### ModelInferenceResult Structure

| Field | Type | Notes |
| --- | --- | --- |
| `step_id` | enum(`STEP_2`..`STEP_7`, `NONE`) | Predicted step from model. |
| `confidence` | float [0,1] | Softmax probability of predicted step. |
| `orientation` | enum(...) | Orientation variant if applicable (derived from landmark asymmetry or model output). |
| `all_probabilities` | map<step_id, float> | Full softmax distribution for logging/debugging. |
| `inference_time_ms` | float | Wall-clock time for inference call. |
| `model_version` | string | Version/hash of loaded model file. |

### Landmark Normalization Contract

Before passing landmarks to the model, apply the following normalization:

1. **Wrist-centering**: Translate all landmarks so the wrist (landmark 0) is at origin (0, 0, 0) per hand.
2. **Scale normalization**: Divide by the distance from wrist to middle finger MCP (landmark 9) to normalize hand size.
3. **Hand ordering**: Always place left hand landmarks before right hand landmarks; pad with zeros if only one hand visible.
4. **Temporal alignment**: Pad incomplete windows with the last valid frame or zeros if session just started.

### Fallback Decision Logic

The `DetectorRunner` SHALL apply the following logic to decide between model and heuristic classification:

```
IF model not loaded:
    USE heuristic detectors
    LOG fallback_event(reason=MODEL_MISSING)
ELSE IF landmark_confidence < config.model.landmark_confidence_min:
    USE heuristic detectors
    LOG fallback_event(reason=LANDMARK_LOW_CONFIDENCE)
ELSE IF landmark_window incomplete (< min_window_frames):
    USE heuristic detectors
    LOG fallback_event(reason=WINDOW_INCOMPLETE)
ELSE:
    RUN model inference
    IF model_result.confidence < config.model.model_confidence_min:
        USE heuristic detectors
        LOG fallback_event(reason=MODEL_LOW_CONFIDENCE, model_confidence=...)
    ELSE:
        USE model_result
        SET source=MODEL
```

## Interpreter Event Bus

| Event | Source | Payload |
| --- | --- | --- |
| `session_started` | Session manager | `{session_id, start_ts, config_version, model_version}` |
| `session_ended` | Session manager | `{session_id, end_ts, summary}` |
| `step_state_update` | Interpreter | `{session_id, step_id, state, orientation, accumulated_ms, confidence, source}` |
| `uncertainty_event` | Interpreter | `{session_id, reason, timestamp_ms}` |
| `fallback_event` | DetectorRunner | `{session_id, reason, timestamp_ms, model_confidence, landmark_confidence}` |
| `model_inference` | LandmarkSequenceClassifier | `{session_id, step_id, confidence, inference_time_ms}` |
| `led_signal` | Feedback bridge | `{step, step_id, state, timestamp_ms, blink_hz}` where state is `CURRENT`, `COMPLETED`, or `IDLE` |

Consumers: logging subsystem, progress reporter, optional ESP8266 publisher.

## Config Schema (YAML/JSON)

```yaml
config_version: "1.0.0"
roi: { x: 120, y: 80, width: 400, height: 360 }
session:
  motion_threshold: 0.4
  relative_motion_threshold: 0.25
  start_window_frames: 5
  stop_timeout_ms: 1500
model:
  enabled: true                          # Whether to attempt model-based classification
  path: "models/step_classifier.onnx"    # Path to pre-trained ONNX or TFLite model file
  format: "onnx"                         # Model format: "onnx" or "tflite"
  fallback_allowed: true                 # If true, run heuristics when model unavailable; if false, refuse to start
  model_confidence_min: 0.6              # Minimum model confidence to use model output
  landmark_confidence_min: 0.5           # Minimum MediaPipe confidence to attempt model inference
  window_frames: 16                      # Number of frames per landmark window (~0.67s at 24 FPS)
  window_stride: 8                       # Frames between window starts (overlap = window_frames - stride)
steps:
  STEP_2:
    duration_ms: 3000  # placeholder pending infection-control validation
    confidence_min: 0.7  # placeholder pending infection-control validation
  STEP_3:
    duration_ms: 3000  # placeholder pending infection-control validation
    confidence_min: 0.7  # placeholder pending infection-control validation
  STEP_4:
    duration_ms: 3000  # placeholder pending infection-control validation
    confidence_min: 0.7  # placeholder pending infection-control validation
  STEP_5:
    duration_ms: 3000  # placeholder pending infection-control validation
    confidence_min: 0.7  # placeholder pending infection-control validation
  STEP_6:
    duration_ms: 3000  # placeholder pending infection-control validation
    confidence_min: 0.75  # placeholder pending infection-control validation
  STEP_7:
    duration_ms: 3000  # placeholder pending infection-control validation
    confidence_min: 0.75  # placeholder pending infection-control validation
esp8266:
  enabled: false
  host: "http://esp8266.local"
  timeout_ms: 500
  blink_hz: 1.0
video_capture:
  enabled: false
  retention_seconds: 0       # optional; use for time-based pruning
  max_sessions: 0            # optional; use for session-count pruning
  storage_path: "/var/tmp/handwash/captures"
demo_recording:
  enabled: false
  output_path: "/var/tmp/handwash/demo_frames"
```

Validation rules:
- All durations/confidence values must be positive (placeholders must be tuned before pilot deployment).
- ROI must fit inside camera resolution.
- Model configuration:
  - If `model.enabled` is true and `model.path` is specified, the file MUST exist and be readable at startup.
  - If `model.enabled` is true but model file is missing/invalid and `model.fallback_allowed` is false, startup MUST fail with a clear error.
  - If `model.enabled` is true but model file is missing/invalid and `model.fallback_allowed` is true, log a warning and continue in heuristic-only mode.
  - `model.format` must be one of `onnx` or `tflite`.
  - `model.window_frames` must be >= 8 and <= 48.
- ESP8266 block optional; if enabled, run a startup smoke test—failures only log a warning, trip the 500 ms timeout, and auto-disable LED signaling for that session.
- `video_capture.enabled` defaults to false; when set true the config MUST provide an absolute `storage_path`. Retention limits are optional.
- `demo_recording.enabled` defaults to false; when set true the config MUST provide an absolute `output_path`.
- Retention policies enforce privacy: the CLI refuses to start if `enabled` is true but retention metadata is missing or invalid, and capture rotation deletes the oldest files first when limits are exceeded (logging each deletion with policy details).
- `retention_seconds` and `max_sessions` are mutually exclusive when both are non-zero; if both are zero, no automated retention is applied.

## ESP8266 Protocol (HTTP POST)

- Endpoint: derived from `esp8266.host` with `/signal` and `/reset` paths
- Method: `POST`
- Headers: `Content-Type: application/json`
- Payload:
```json
{
  "step": 5,
  "step_id": "STEP_5",
  "state": "CURRENT", // or "COMPLETED" or "IDLE"
  "timestamp_ms": 1703400000000,
  "blink_hz": 1.0
}
```
- Success: HTTP 200; Failure: log warning, disable LED signaling for the session, and continue without retry.

## Demo Mode Replay Contract

- Demo assets: `.npz` files containing synchronized frame timestamps + landmark arrays; optional ground-truth step labels exist for a curated subset.
- Replay script feeds `FramePacket` objects through detectors and interpreter.
- Output: deterministically reproduces session logs and status output (ground-truth comparisons when available, otherwise invariant checks).
