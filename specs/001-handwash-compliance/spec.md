# Feature Specification: On-Device WHO Steps 2-7 Compliance

**Feature Branch**: `001-handwash-compliance`  
**Created**: 2026-01-10  
**Status**: Draft  
**Input**: User description: "On-device handwashing compliance (WHO rubbing steps 2-7) with timing, progress, logging, and optional ESP8266 LED feedback."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Session Auto-Start/Stop (Priority: P1)
When two hands enter the configured washing-zone region of interest (ROI) in the camera frame and exhibit sustained rubbing-like motion above configurable thresholds, the system must open a monitoring session, initialize step states, and close the session when hands leave the ROI or motion subsides beyond the timeout.

**Rubbing-like motion definition (for gating)**:
- Compute per-frame hand motion as the mean 2D landmark velocity (pixels/frame) across all visible landmarks for both hands, plus the mean relative palm-to-palm motion magnitude.
- Compute a short-window average over `session.start_window_frames` (default 5) for both motion terms.
- Motion is considered "rubbing-like" when both (a) mean landmark velocity >= `session.motion_threshold` and (b) mean relative palm motion >= `session.relative_motion_threshold` for the full window.
- These metrics are thresholded in pixel units per frame; ROI scaling must be applied consistently so thresholds remain stable across resolutions.

**Why this priority**: Without reliable ROI-aware session boundaries, timing, logging, and analytics cannot align to real washing attempts.

**Independent Test**: Replay recorded sink footage with known ROI overlays; verify session start/end timestamps and baseline state initialization occur only when both ROI presence and motion thresholds are met.

**Acceptance Scenarios**:

1. **Given** the system is idle and the washing-zone ROI is configured, **When** two hands enter that ROI and sustain rubbing-like motion above the configured motion threshold for the recognition window, **Then** a new session starts within 1 second and all step states initialize to "not started."
2. **Given** a session is active, **When** both hands leave the ROI or motion falls below the threshold for longer than the configurable timeout, **Then** the session ends, the summary record is sealed, and no additional timing accrues. Temporary loss of one hand below the timeout does not immediately end the session.

---

### User Story 2 - WHO Step Recognition (Priority: P2)
During an active session, the system classifies the current WHO step (2-7) per the canonical definitions below, emitting step identifiers with confidence scores; steps 3, 6, and 7 are treated as single steps with left/right orientation variants rather than separate steps.

Classification is performed by a **LandmarkSequenceClassifier** that runs inference on sliding windows of normalized MediaPipe landmarks using a pre-trained model file. When the model is unavailable or confidence is low, the system falls back to heuristic detectors.

**Why this priority**: Accurate per-step classification drives timing, progress visibility, and compliance reporting.

**Independent Test**: Feed labeled landmark sequences for each canonical step (including orientation variants) to confirm the classifier outputs the correct step identifier plus orientation metadata and confidence values; verify fallback to heuristics when model confidence is below threshold.

**Acceptance Scenarios**:

1. **Given** hands perform canonical Step 3 with right palm over left dorsum, **When** the cues remain visible for the recognition window, **Then** the system labels it as "Step 3" with orientation "right-over-left" and confidence above the configured threshold. 
2. **Given** more than two hands appear in the ROI or hand assignment becomes ambiguous, **When** classification would otherwise proceed, **Then** the system sets detection state to "uncertain," avoids emitting a step completion, and logs the ambiguity event for the session record. 

---

### User Story 3 - Per-Step Timing & Completion (Priority: P3)
Using the classification events from User Story 2, the system accumulates confident time per step and marks a step complete only when its configurable minimum duration is satisfied; steps may complete in any order.

**Why this priority**: Infection-control policy depends on minimum rubbing time per canonical step, not just gesture recognition.

**Independent Test**: Run synthetic landmark timelines with staged classification/confidence events to confirm accumulated time matches expectations and completion toggles exactly at threshold crossings.

**Acceptance Scenarios**:

1. **Given** Step 4 classification events remain confident, **When** the accumulated confident_ms for Step 4 reaches its configured duration threshold, **Then** the interpreter transitions the step to "completed" and logs the total milliseconds spent.
2. **Given** Step 5 is in progress, **When** classification confidence drops below the threshold or becomes uncertain, **Then** timing pauses without resetting, and it resumes from the last accumulated value once confidence recovers, unless the session ends.

---

### User Story 4 - Demo-Friendly Progress Reporting (Priority: P4)
The system must expose a real-time status output that shows each canonical step as not started, in progress, or completed, plus highlight the current step for demo observers using the standardized console text grid defined below.

**Why this priority**: Hackathon stakeholders need immediate insight without additional UI investment; status output also validates interpreter state during development.

**Independent Test**: Use deterministic demo mode to drive a known sequence and confirm the status output updates within the expected latency and matches logged events.

**Acceptance Scenarios**:

1. **Given** a demo session is running, **When** the interpreter transitions a step to "in progress," **Then** the console grid updates within 500 ms, prefixes the corresponding row with the `>` marker, and sets the state column to `IN_PROGRESS` while leaving other rows unchanged.
2. **Given** Step 5 completes during demo replay, **When** deterministic fixtures drive the interpreter, **Then** the status grid row for Step 5 changes its state column to `COMPLETED`, freezes its accumulated milliseconds, replaces the leading marker with `*`, and the `>` marker advances to the next active step within 500 ms.

#### Console Status Grid Format

- Render a fixed 7-row grid (header + steps 2-7 in numeric order) with the literal columns `STEP | STATE | MS` and a dashed separator so demo scripts can parse the output deterministically.
- Each step row begins with a single-character marker: a space (` `) for not started, `>` for the current step, and `*` for completed steps. Only one row may show `>` at a time.
- The `STATE` column MUST use the uppercase tokens `NOT_STARTED`, `IN_PROGRESS`, or `COMPLETED` and reflect interpreter state changes without abbreviation.
- The `MS` column displays zero-padded millisecond totals (width 5) accumulated for the step; completed rows freeze the reported value until the session ends.
- The grid refreshes at most twice per second (500 ms cadence) and overwrites the prior grid in place to keep the console readable over SSH/HDMI.

**Example**

```
STEP | STATE        | MS
------------------------
*2   | COMPLETED    | 04000
>3   | IN_PROGRESS  | 00120
 4   | NOT_STARTED  | 00000
 5   | NOT_STARTED  | 00000
 6   | NOT_STARTED  | 00000
 7   | NOT_STARTED  | 00000
```

---

### User Story 5 - Structured Logging & Aggregation (Priority: P5)
Each session produces a structured record covering step outcomes, timing, uncertainty intervals (including ROI ambiguity), and config references; aggregate analytics summarize misses and averages over time.

**Why this priority**: Infection-prevention teams need audit trails and insights to tune training and thresholds.

**Independent Test**: Run multiple recorded sessions, inspect generated JSON/CSV logs, and compute aggregates to verify metrics such as most-missed step and average completion time per canonical step.

**Acceptance Scenarios**:

1. **Given** multiple sessions run, **When** logs are exported, **Then** each record includes session_id, config_version, per-step states, accumulated time, uncertainty markers (e.g., ROI ambiguity), and total rubbing time.
2. **Given** aggregate analytics are requested, **When** the system processes historical logs, **Then** it returns the most-missed step, per-step averages, and failure pattern summaries tied to canonical step identifiers.

---

### User Story 6 - Optional ESP8266 LED Feedback (Priority: P6)
After core detection is reliable, the Raspberry Pi may share step completion events with an ESP8266 over WiFi so LEDs mirror progress (solid for completed steps, 1 Hz blinking for the current step with a 50% duty cycle) without impacting core detection if unavailable.

**Why this priority**: Visual feedback at the sink demonstrates compliance to users and hackathon judges without additional UI development.

**Independent Test**: Use a stubbed or real ESP8266 to confirm messages arrive, LEDs toggle as expected when available, and network failures are logged without disrupting detection.

**Acceptance Scenarios**:

1. **Given** the Pi marks Step 5 complete, **When** WiFi connectivity is available, **Then** the ESP8266 receives the event and lights the Step 5 LED solid within 1 second.
2. **Given** the interpreter highlights Step 6 as the current step, **When** LED feedback is enabled, **Then** the corresponding LED blinks at exactly 1 Hz with a 50% duty cycle (500 ms on, 500 ms off) until the step completes or the session ends.
3. **Given** the WiFi link drops mid-session, **When** the interpreter continues detecting steps, **Then** the LED subsystem logs the failure, skips the affected update, and core detection plus logging continue normally without retries or buffering guarantees.

#### LED Signaling Behavior

- Each LedSignal payload references a canonical step plus one of three states: `CURRENT`, `COMPLETED`, or `IDLE`.
- `CURRENT` signals instruct the ESP8266 firmware to blink the LED at 1 Hz with a 50% duty cycle (500 ms on, 500 ms off) until another step becomes current or the session ends.
- `COMPLETED` signals illuminate the LED solid (no blink) until the session resets; LEDs never re-enter blink mode once a step is marked completed.
- Steps that are `NOT_STARTED` emit implicit `IDLE` (LED off) and never send traffic to the ESP8266 until they transition to current or completed.
- The Raspberry Pi disables LED integration automatically for the remainder of a session after any timeout/failure event to guarantee core detection latency.

### Edge Cases

- Hands briefly leave the camera frame mid-step and re-enter (tracking continuity vs. timeout).
- Multiple people enter the washing zone simultaneously, causing ambiguous landmarks and forcing the "uncertain" state.
- Highly reflective sinks or water droplets cause transient detection noise.
- Invalid or missing configuration files at startup.
- Sessions where none of the steps reach completion thresholds (should still log).
- Camera or ESP8266 temporarily unavailable during a session.

### Non-Goals

- Detecting WHO steps 0-1 or 8-11 as distinct steps.
- Any cloud connectivity, accounts, or identity recognition.
- Enforcing a fixed order for steps 2-7.
- Persisting raw camera feeds is allowed when explicitly enabled in config and governed by retention limits.

### Explicit Out-of-Scope (ML)

- **Data labeling**: Annotating landmark sequences with ground-truth step labels is performed externally; this repository consumes labeled datasets only for validation.
- **Model training**: Training, fine-tuning, or retraining the landmark-sequence classifier is performed offline on separate infrastructure; this repository only loads and runs pre-trained models.
- **Hyperparameter tuning**: Model architecture decisions, learning rates, augmentation strategies, etc. are external concerns.
- **End-to-end vision models**: Image-based CNNs operating on raw frames (bypassing MediaPipe landmarks) are not supported.
- **On-device training or adaptation**: The Raspberry Pi performs inference only; no online learning or model updates occur on-device.
- **Medical-grade validation claims**: The system is for demonstration and operational feedback; it does not provide clinically validated compliance certification.

### Assumptions

- The washing zone is a configurable region of interest (ROI) defined in frame coordinates.
- Classification confidence is evaluated over a short, configurable recognition window.

### Modeling Assumptions

- **MediaPipe Hands** is responsible only for landmark extraction (21 3D keypoints per hand per frame); it does not classify WHO steps.
- **LandmarkSequenceClassifier** is a separate component that consumes a pre-trained model file (ONNX or TFLite format) trained offline and stored as a deployment artifact.
- The model accepts short sliding windows of normalized landmarks (~0.5–1.0 s) and outputs a WHO step ID (2–7 or `NONE`) plus a confidence score.
- Model training, labeling, hyperparameter tuning, and optimization are **out of scope** for this repository; the system only performs inference using a supplied model file.
- The Raspberry Pi 5 performs CPU-only inference; no GPU or neural accelerator is assumed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically start and end sessions only when hands enter/leave the configured ROI and sustain rubbing-like motion above the configurable thresholds described in User Story 1.
- **FR-002**: System MUST recognize WHO steps 2-7 per the canonical definitions in this document, treating steps 3, 6, and 7 as single steps with orientation variants and ignoring non-canonical motions.
- **FR-003**: System MUST allow steps 2-7 to be completed in any order without blocking later detection.
- **FR-004**: System MUST accumulate confident dwell time per step based on User Story 2 classification events and mark completion only when the configurable duration threshold for that step is met.
- **FR-005**: System MUST expose per-step states (not started / in progress / completed) plus the current focus step via the standardized console grid (`STEP | STATE | MS`, markers `>`/`*`/space) that refreshes within 500 ms of interpreter changes and is parsable over SSH/HDMI.
- **FR-006**: System MUST log per-session records capturing session_id, config_version, per-step timing, completion state, uncertainty intervals (including ROI ambiguity), and total rubbing time.
- **FR-007**: System MUST maintain aggregated analytics that report most-missed step, average time per step, and common failure patterns based on logged sessions.
- **FR-008**: System MUST provide deterministic demo mode that replays curated landmark/video sequences and drives the same outputs as live detection.
- **FR-009**: System MUST enforce configuration-driven thresholds (timing, confidence, timeouts, ROI bounds) loaded from validated files and refuse to run with invalid configs.
- **FR-010**: System MUST enter or remain in an "uncertain" state, without marking step completion, whenever detector confidence drops below threshold or more than two hands/ambiguous assignments appear, and MUST log these events.
- **FR-011**: System MUST (optionally) publish step completion events to an ESP8266 over WiFi, logging any transmission failures without retry or buffering guarantees and without crashing core detection.
- **FR-012**: System MUST NOT persist raw video by default; when video recording is enabled by config, capture artifacts are permitted and remain excluded from compliance scoring, detector logic, and analytics aggregation. Retention controls are optional and may be manual.

### Training Data Export Requirements

- **FR-019**: System MUST expose a CLI-controlled training export mode that writes each capture run into a unique session directory (UTC timestamp with suffixes) containing both a `landmarks.jsonl` file and a synchronized `video.mp4`, ensuring runs never overwrite prior data.
- **FR-020**: Each exported landmark entry MUST log the timestamp in seconds since the capture started, include structured `left_hand` and `right_hand` arrays (21 × [x, y, z] triples) plus optional hand confidence, and align with the MP4 stream so offline labelers can scrub the video and annotate time ranges directly from the JSONL feed.
- **FR-021**: Training export mode MUST remain inference-only; the Raspberry Pi may collect synchronized data but MUST NOT perform labeling, augmentation, or any on-device training.

### Model-Based Step Detection Requirements

- **FR-013**: System MUST accept a pre-trained landmark-sequence model file (ONNX or TFLite format) as an input artifact at startup; the model file path is specified in the configuration.
- **FR-014**: System MUST classify WHO steps from temporal landmark sequences (sliding windows of ~0.5–1.0 s) rather than single-frame heuristics when the model is available and valid.
- **FR-015**: System MUST expose model inference confidence scores to downstream logic (interpreter, logging, progress reporting) alongside the predicted step ID.
- **FR-016**: System MUST fall back to heuristic detectors when:
  - (a) the model file is missing, invalid, or fails to load at startup;
  - (b) MediaPipe landmark confidence is below the configured threshold for the current window;
  - (c) model inference confidence is below the configured `model_confidence_min` threshold.
- **FR-017**: System MUST log fallback events with reason codes (`model_missing`, `model_invalid`, `landmark_low_confidence`, `model_low_confidence`) for observability.
- **FR-018**: System MUST validate the model file at startup (format, input/output shape, version metadata) and refuse to run if validation fails and no fallback is allowed by config.
### Key Entities *(include if feature involves data)*

- **SessionRecord**: Unique session identifier, timestamps, config_version, per-step StepStatus records, uncertainty events (confidence drops, ROI ambiguity), total rubbing duration, optional demo flag.
- **StepStatus**: Step_id (2-7), orientation_variant flag (left/right when applicable), current state, accumulated_confident_ms, completion timestamp, count of uncertainty intervals.
- **ConfigProfile**: Versioned structure containing ROI coordinates, per-step duration thresholds, confidence minimums, session timeout, LED enable flags, demo-mode parameters, an optional `demo_recording` block with `enabled` (bool, default false) and `output_path` (absolute directory for annotated frames), and an optional `video_capture` block with storage settings and optional retention controls.
- **DemoRecordingArtifact**: Collection of annotated output frames (ROI + step status overlays) generated when demo recording is enabled; stored separately from session logs and ignored by detectors, interpreter logic, and analytics.
- **VideoCaptureArtifact**: Optional raw video files or frame sequences written when `video_capture.enabled` is true; ignored by compliance, detector logic, and analytics.
- **AggregateStats**: Rolling metrics derived from SessionRecord entries, including most_missed_step, average_step_time, and frequent failure patterns.
- **LedSignal**: Minimal payload describing step_id, LED state (`CURRENT`, `COMPLETED`, `IDLE`), timestamp, duty-cycle metadata (always 1 Hz, 50% for `CURRENT`), and whether the signal was delivered or logged as failed.

### Non-Functional Requirements: Model Inference

- **NFR-ML-001**: Model inference latency MUST NOT exceed **5 ms per window** on Raspberry Pi 5 (CPU-only, single Cortex-A76 core) to preserve the >=24 FPS pipeline target.
- **NFR-ML-002**: Model file size MUST NOT exceed **10 MB** to allow fast startup and fit comfortably in Pi 5 memory alongside MediaPipe.
- **NFR-ML-003**: If the model file is missing at startup:
  - When `model.fallback_allowed` is `true` (default), log a warning and operate in heuristic-only mode for the session.
  - When `model.fallback_allowed` is `false`, refuse to start and exit with a non-zero code.
- **NFR-ML-004**: If the model file is present but fails validation (incompatible format, wrong input shape, corrupt data), log the validation error and apply the same fallback logic as NFR-ML-003.
- **NFR-ML-005**: Model loading and validation MUST complete within **2 seconds** at startup to avoid blocking the capture pipeline.

### Per-Step Timing Defaults

- Until formal infection-control guidance is provided, WHO Steps 2-7 share a **demo default** minimum dwell time of **3.0 seconds per step** (`duration_ms = 3000`).
- These defaults ship in `config/example.yaml` and are intended for hackathon demos; operators may override them in the config file at deploy time without code changes.
- Tests and acceptance criteria reference the configured values, so when real thresholds are approved only the config (not the spec) must be updated.

### Video Recording & Demo Artifacts (Optional)

- `demo_recording.enabled` defaults to `false`; when enabled, the system writes annotated output frames (ROI outlines + per-step console status overlays) to `demo_recording.output_path`.
- `video_capture.enabled` defaults to `false`; when enabled, the system may store raw video or frame sequences to `video_capture.storage_path` and may optionally apply `retention_seconds` or `max_sessions` limits.
- Both demo recordings and video captures are optional artifacts for demo/debug; they do not influence compliance scoring, detector logic, or analytics.

### Training Export Data Contract

- Each export run creates `recordings/training_exports/<UTC timestamp>` (e.g., `20260110T231030/`). Tie-break suffixes (`-01`, `-02`, …) prevent overwrites when multiple captures start within the same second.
- Every folder contains:
  - `landmarks.jsonl`: newline-delimited JSON objects.
  - `video.mp4`: MP4 encoded at operator-selected FPS (default 24 FPS) with the first frame captured at the same instant as the first JSON entry.
- JSON schema per frame:

```json
{
  "timestamp_s": 1.208,
  "step_id": "STEP_3",
  "orientation": "RIGHT_OVER_LEFT",
  "left_hand": {
    "landmarks": [[0.12, 0.42, -0.03], [0.18, 0.47, -0.05]],
    "confidence": 0.93
  },
  "right_hand": null
}
```

- `timestamp_s` is always seconds since the export session began (float). Null hands indicate missing detections; arrays always contain 21 triples with normalized coordinates.
- Example snippet truncates the landmark array for readability; the exporter always writes all 21 landmark triples per detected hand in chronological order.
- Optional metadata such as `step_id`/`orientation` annotate the capture but do not affect the labeling workflow.
- Because the JSON and MP4 share the same time origin, reviewers can scrub the video using the JSON timestamps without drift; the Pi never interpolates or resamples the landmark timeline.

### ROI Calibration Workflow

- Operators launch `deltawash_pi/cli/roi_calibrate.py`, which shows the live camera feed with a rectangular ROI overlay sourced from the current config.
- Using keyboard controls (documented in the CLI help), the operator drags/resizes the rectangle until both hands remain fully inside the ROI during normal washing motions at the sink.
- Once satisfied, the CLI saves the updated coordinates back to the config file and validates that the ROI lies within the camera resolution.
- Acceptance criterion: sessions may only auto-start when both hands are fully inside the configured ROI; partial entry or hands outside the rectangle must keep the system idle.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Achieve at least 85% correct step completion labeling on a curated 30-session demo dataset with diverse orientations (hackathon-scoped assumption tied to that dataset).
- **SC-002**: Maintain on-device processing latency under 200 ms per frame (approx. 24 FPS) on Raspberry Pi 5 during live sessions.
- **SC-003**: Produce structured per-session logs and aggregated analytics with 100% of sessions containing config_version references and per-step timing breakdowns.
- **SC-004**: Update progress output (console/overlay or equivalent) and optional LED signals within 500 ms of interpreter state changes in demo mode.

## Canonical WHO Step Definitions (2-7)

### Step 2 - Palm-to-Palm Rubbing
- **Posture**: Both palms face each other with minimal gap; fingers relaxed but aligned.
- **Motion**: Symmetric back-and-forth sliding between palms generating friction.
- **Key cues**: Palms stay aligned, little relative rotation, motion confined to palm plane.

### Step 3 - Palm Over Opposite Dorsum with Interlaced Fingers (Variants: right-over-left, left-over-right)
- **Posture**: One palm contacts the back (dorsum) of the opposite hand with fingers interlaced.
- **Motion**: Rubbing stroke of the upper palm across the dorsum while the lower hand stays oriented outward.
- **Key cues**: Alternating fingers weaving together, asymmetric contact with a clear "top" and "bottom" hand.

### Step 4 - Palm-to-Palm with Interlaced Fingers
- **Posture**: Palms face one another with fingers interlaced fully.
- **Motion**: Rubbing occurs while interlocked fingers move as a unit, distinct from Step 2 due to finger weaving.
- **Key cues**: Interlacing maintained, palm centers aligned, no dorsal surfaces exposed.

### Step 5 - Backs of Fingers to Opposing Palm with Fingers Interlocked
- **Posture**: Hands rotate so the backs of fingers press against the opposite palm while fingers hook together.
- **Motion**: Side-to-side or back-and-forth rubbing where knuckles contact the opposite palm.
- **Key cues**: Dorsal finger surfaces touching palm surfaces, hooked finger posture, limited palm-to-palm contact.

### Step 6 - Rotational Rubbing of Thumb Clasped in Opposite Palm (Variants: left-thumb, right-thumb)
- **Posture**: One thumb is enclosed by the opposite hand's palm and fingers.
- **Motion**: Circular rubbing motion around the thumb using the opposite hand, resembling twisting a handle.
- **Key cues**: Thumb isolated, clasp pressure evident, rotational motion centered on the thumb joint.

### Step 7 - Rotational Rubbing of Fingertips in Opposite Palm (Variants: left-fingertips, right-fingertips)
- **Posture**: Fingertips of one hand cluster together and press into the opposite palm center.
- **Motion**: Small circular rubbing to clean fingertips/under nails.
- **Key cues**: Fingertips localized to palm center, circular motion without interlacing, focus on distal phalanges.

## Review & Acceptance Checklist

- Constitution alignment (scope limited to WHO 2-7, on-device, config-driven) - OK
- Traceability (each FR maps to at least one user story and acceptance scenario) - OK
- Open questions resolved or tracked via future specs - OK
