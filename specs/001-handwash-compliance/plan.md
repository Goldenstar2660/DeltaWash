# Implementation Plan: On-Device WHO Steps 2-7 Compliance

**Branch**: `001-handwash-compliance` | **Date**: 2026-01-10 | **Spec**: specs/001-handwash-compliance/spec.md
**Input**: Feature specification from `/specs/001-handwash-compliance/spec.md`

## Summary
Build a Raspberry Pi 5 on-device system that detects WHO hand-rubbing Steps 2-7 via MediaPipe Hands landmark extraction and a pre-trained **LandmarkSequenceClassifier**, accumulates per-step timing through modular detectors plus an event-driven interpreter, logs structured session data, provides demo-friendly progress output, and optionally mirrors completion through ESP8266 LEDs. The MVP prioritizes reliable session gating, sequence-based classification, timing, logging, and deterministic demo playback; LED feedback is phase-gated until the core loop is stable.

## Technical Context

**Language/Version**: Python 3.11 on Raspberry Pi OS Bookworm 64-bit  
**Primary Dependencies**: MediaPipe Hands, OpenCV, NumPy, ONNX Runtime (CPU), requests-style HTTP client (short timeouts)  
**Model Artifact**: Pre-trained ONNX or TFLite model file for landmark-sequence classification (trained offline, not in this repository)  
**Storage**: JSON Lines per-session logs, JSON aggregates, YAML/JSON config files  
**Testing**: pytest (unit + integration), CLI smoke scripts, deterministic demo comparison  
**Target Platform**: Raspberry Pi 5 (4 GB) with Pi Camera Module 3  
**Project Type**: Single-device Python package with CLI entry points  
**Performance Goals**: >=24 FPS sustained; <200 ms capture-to-status latency; LED updates <500 ms  
**Constraints**: Fully offline, config-driven thresholds, fail-safe "uncertain" state, no raw video storage by default (optional recording allowed; retention optional)  
**Scale/Scope**: Single sink deployment; curated 30-session dataset for validation

## Constitution Check

1. **Spec-Driven Scope Discipline**: Scope limited to WHO Steps 2-7, on-device only. OK
2. **Modular On-Device Architecture**: Detectors, interpreter, logging, feedback isolated. OK
3. **Real-Time Reliability & Fail-Safe**: FPS budget, uncertainty handling, camera/ESP8266 failure plans included. OK
4. **Observability & Analytics**: Structured per-session logs and aggregate stats planned. OK
5. **Verification, Privacy & Demo Readiness**: Unit/integration/smoke tests plus deterministic demo workflow defined. OK

## Project Structure

```
src/
|-- deltawash_pi/
|   |-- detectors/
|   |   |-- step2.py
|   |   |-- step3.py
|   |   |-- step4.py
|   |   |-- step5.py
|   |   |-- step6.py
|   |   |-- step7.py
|   |-- interpreter/
|   |   |-- state_machine.py
|   |   |-- session_manager.py
|   |-- feedback/
|   |   |-- status.py
|   |   |-- esp8266.py
|   |-- logging/
|   |   |-- sessions.py
|   |   |-- aggregates.py
|   |-- config/
|   |   |-- loader.py
|   |-- demo/
|   |   |-- replay.py
|   |-- cli/
|       |-- capture.py
|       |-- demo.py
|       |-- analytics.py
|       |-- led_test.py
|       |-- smoke_camera.py
|       |-- roi_calibrate.py
|-- tests/
    |-- unit/
    |   |-- test_detectors.py
    |   |-- test_timing.py
    |   |-- test_config.py
    |-- integration/
    |   |-- test_interpreter.py
    |-- smoke/
        |-- test_demo_mode.py
```

**Structure Decision**: Single Python package keeps detectors, interpreter, logging, and feedback isolated for substitution and focused testing while providing CLI entry points for capture, demo replay, analytics, and smoke checks.

## Architecture: Detection Pipeline

The detection pipeline consists of the following components:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Capture Pipeline (CLI)                        │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ FramePacket (frame, timestamp, ROI)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    MediaPipe Hands (Landmark Extraction)             │
│  - Extracts 21 3D keypoints per hand per frame                       │
│  - Reports hand count, handedness, tracking confidence               │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ FramePacket + landmarks + confidence
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│              LandmarkSequenceClassifier (ML Inference)               │
│  - Loads pre-trained ONNX/TFLite model at startup                    │
│  - Buffers ~0.5–1.0 s of normalized landmark windows                 │
│  - Runs inference on demand, outputs step_id + confidence            │
│  - Falls back to heuristics when model/confidence unavailable        │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ ModelInferenceResult (step_id, confidence, source)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Heuristic Detectors (Fallback)                  │
│  - Step2Detector ... Step7Detector                                   │
│  - Geometric threshold-based classification                          │
│  - Used when ML model unavailable or low confidence                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ StepSignal (step_id, orientation, confidence, source)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         DetectorRunner                               │
│  - Orchestrates ML classifier + heuristic fallback                   │
│  - Merges signals, applies confidence gating                         │
│  - Emits unified StepSignal stream to interpreter                    │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ StepSignal stream
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  Interpreter (State Machine + Timing)                │
│  - Accumulates confident dwell time per step                         │
│  - Manages step state transitions (NOT_STARTED → IN_PROGRESS → COMPLETED) │
│  - Emits step_state_update events                                    │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ Events
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │  Logging  │   │  Status   │   │   LED     │
        │  (JSONL)  │   │ Reporter  │   │ (ESP8266) │
        └───────────┘   └───────────┘   └───────────┘
```

### Component Responsibilities

| Component | Responsibility | Input | Output |
|-----------|----------------|-------|--------|
| MediaPipe Hands | Landmark extraction only | RGB frame | 21×3 landmarks per hand, confidence |
| LandmarkSequenceClassifier | ML-based step classification | Landmark window buffer | `ModelInferenceResult` (step_id, confidence) |
| Heuristic Detectors | Geometric fallback classification | Single FramePacket | `StepSignal` per step |
| DetectorRunner | Orchestration, fallback logic | FramePacket | Unified `StepSignal` stream |
| Interpreter | Timing, state management | StepSignal stream | State events |

### Model File Requirements

- **Format**: ONNX (preferred) or TFLite for CPU inference
- **Input shape**: `[batch, window_frames, landmarks]` where `landmarks = 42` (two hands × 21 keypoints) or `63` (single hand × 21 × 3D)
- **Output shape**: `[batch, num_classes]` with softmax probabilities for steps 2–7 plus NONE
- **Location**: Specified in config as `model.path`; validated at startup
- **Trained offline**: Model training, labeling, and optimization occur outside this repository

## Phased Plan

### Phase 0: Foundations & Research (1 day)
- Benchmark MediaPipe Hands + OpenCV ROI cropping at 640x480 on Pi 5 to confirm >=24 FPS.
- Benchmark ONNX Runtime CPU inference latency for target model architecture (~1D CNN with 16-frame window) to confirm <5 ms per inference.
- Capture short landmark sequences for each step/orientation; store as fixtures.
- Finalize ESP8266 HTTP POST payload and timeout expectations (documented in contracts).

### Phase 1: Core Infrastructure (2 days)
- Implement config loader/validator (ROI, motion thresholds incl. relative motion, timeouts, ESP8266 block, model block with path/fallback settings, demo_recording, video_capture storage and optional retention) with schema enforcement and startup refusal on invalid files.
- Implement model loader and validator in `src/deltawash_pi/detectors/model_loader.py` that loads ONNX/TFLite files, validates input/output shapes, and exposes the inference session.
- Build ROI-aware session manager that only opens a session when exactly two hands are detected within the configured ROI *and* rubbing-like motion stays above thresholds for the start window, and ends sessions when either condition drops out beyond the timeout.
- Create `FramePacket` abstraction bundling frame, landmarks, ROI metadata, motion metrics, config hash.
- Implement JSONL session logger referencing config_version and placeholder StepStatus records.
- Add deterministic demo replay skeleton to feed recorded fixtures through later modules.
- Integrate optional demo recording and video capture hooks into the capture pipeline, with optional retention when configured by profile.

### Phase 2: Detector Modules (3 days)
- Implement `LandmarkSequenceClassifier` in `src/deltawash_pi/detectors/sequence_classifier.py`:
  - Buffers normalized landmark windows (~16–24 frames, 0.5–1.0 s at 24 FPS)
  - Normalizes landmarks (wrist-centered, scale-invariant, hand-order consistent)
  - Runs ONNX/TFLite inference on demand
  - Outputs `ModelInferenceResult` with step_id, confidence, inference_time_ms
- Implement detector base class handling shared config, orientation metadata, and confidence gating (fallback path).
- Build per-step heuristic detectors (2-7) aligned to canonical definitions as fallback when model confidence is low or model unavailable.
- Implement `DetectorRunner` that:
  - Invokes `LandmarkSequenceClassifier` first when model is available
  - Falls back to heuristic detectors when model confidence < threshold or model unavailable
  - Logs fallback events with reason codes
  - Emits unified `StepSignal` stream with `source` field indicating `model` or `heuristic`
- Write unit tests per detector and classifier using synthetic landmarks to validate confident vs uncertain transitions and orientation tagging.
- Measure combined detector + inference latency to ensure pipeline keeps >=24 FPS.

### Phase 3: Interpreter & Timing (3 days)
- Implement interpreter state machine that consumes detector signals, manages per-step states, accumulates time, and enforces the "uncertain" halt rules.
- Integrate session manager lifecycle to reset states on start/stop and emit `session_started`/`session_ended` events.
- Build console status reporter (text grid) showing per-step state + accumulated ms with <500 ms refresh latency.
- Unit tests for timing accumulation, pause/resume on confidence loss, and completion threshold enforcement.
- Integration tests feeding scripted detector outputs covering out-of-order steps and ambiguity events.

### Phase 4: Observability & Analytics (2 days)
- Extend session logger with uncertainty events, ROI info, orientation metadata.
- Implement aggregation CLI computing most-missed step, average times, uncertainty frequencies from logs.
- Add smoke test verifying camera reconnect handling and log integrity when camera restarts mid-session.

### Phase 5: Demo Mode & Deterministic Validation (1 day)
- Finish demo CLI to replay curated dataset, using optional ground-truth labels for a small subset plus invariant checks (state transitions, completion thresholds, log schemas) to confirm deterministic behavior.
- Document demo workflow and validation steps in quickstart.

### Phase 6: Optional ESP8266 Feedback (2 days)
- Implement synchronous ESP8266 HTTP client that triggers on step completion events with sub-500 ms timeouts so LED signaling never blocks the detection loop.
- Provide CLI utility to send ad-hoc LED signals for wiring tests; if the configured endpoint is unreachable, log a warning, disable LED signaling for the session, and continue detection/logging normally.
- Update quickstart with LED wiring, configuration, troubleshooting guidance.

### Phase 7: Polish & Handoff (1 day)
- Finalize quickstart, data model, research notes, and contracts with any implementation tweaks.
- Run full smoke suite: camera capture, demo replay, integration tests, ESP8266 check (if enabled).
- Record known issues and follow-up tasks for outstanding clarifications (step durations, ROI coordinate guidance, etc.).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate detector modules | Required by constitution for modularity and per-step tuning | Single monolithic detector blocks targeted testing/tuning |
| Optional ESP8266 subsystem | Needed for hackathon visual feedback yet must stay decoupled | Embedding LED control inside interpreter risks crashes when WiFi absent |

## Testing Strategy
- **Unit**: pytest suites covering detectors, timing accumulator, config validation, ROI session manager, LED client stubs.
- **Integration**: Simulated session pipeline feeding scripted detector outputs to interpreter and verifying state progression, logging, and LED signals (when enabled).
- **Smoke**: Camera pipeline script measuring FPS and reconnect resilience; LED HTTP test script; ROI overlay/calibration CLI.
- **Demo Regression**: Deterministic replay comparing generated session logs/status output against golden fixtures.

## Phase 9 Verification Log (2026-01-10)
- `pytest tests/smoke -q` → **9 tests passed** in 1.71 s (MediaPipe/detector/LED smoke coverage intact).
- `python -m deltawash_pi.cli.capture --config config/local.yaml --mock-session --mock-frames 60 --log-steps` → mock capture loop exercised CLI wiring and reproduced LED auto-disable when the configured endpoint `http://192.168.4.50/signal` timed out at 500 ms (expected fail-safe). Session never closed because `min_hands=1`, so no JSONL was written.
- `python -m deltawash_pi.cli.capture --config config/example.yaml --mock-session --mock-frames 80` → stricter config emitted `session_ended` and persisted one log at `logs/sessions/2026-01-10.jsonl` (session_id `375275f4-c855-403e-b43b-3d61a643356d`).
- `python -m deltawash_pi.cli.capture --config config/local.yaml --demo-asset sample-sequence` and `python -m deltawash_pi.cli.demo --config config/local.yaml --asset sample-sequence --verify` → deterministic replay confirmed interpreter state transitions; LED client again disabled itself when ESP8266 was unreachable. Demo capture never emits `session_ended`, so demo-mode entries are not logged.
- `python -m deltawash_pi.cli.smoke_camera --config config/local.yaml --frames 200 --mock` → latency benchmark held **mean=6.1 ms / p95=6.1 ms**, approximated FPS 163.8 (> target 24 FPS, <200 ms budget).
- `python -m deltawash_pi.cli.analytics summarize --logs logs/sessions --out logs/aggregates/summary.json` → aggregates rebuilt (`sessions_count=1`, `model_usage_rate=1.0`, `avg_inference_time_ms≈0.0148`, no uncertainty/fallback events).
- `python -m deltawash_pi.cli.analytics accuracy --manifest demos/manifest.json --logs logs/sessions --out logs/aggregates/summary.json --threshold 0.85` → **fails** (`No demo-mode sessions...`). Root cause: capture demo streams never trigger `session_ended`, so the logger cannot emit `demo_mode=true` records; accuracy CLI intentionally ignores mock-only logs.

**Follow-up**: add a capture/DemoReplay flush that injects a no-hands packet (or explicit logger close) after demo assets finish so demo-mode sessions persist; alternatively seed labeled demo logs under `logs/sessions/` for CI accuracy checks.

## Dependencies & Risks
- ROI coordinates are defined directly in config files; provide an overlay helper and instructions in quickstart so operators can edit values without a separate calibration profile.
- Lighting variability may reduce MediaPipe confidence; log FPS/confidence metrics and surface alerts.
- ESP8266 availability is not guaranteed; keep feature disabled by default and ensure HTTP timeouts are short to avoid blocking.
- Config drift without validation could break detection; enforce schema checks at startup and log config_version in every session.
- Video capture can grow storage quickly; document storage expectations and honor retention limits when configured.

## Deliverables Checklist
- [x] plan.md (this document)
- [x] contracts/interfaces.md (detector + protocol definitions)
- [x] data-model.md (session + aggregate schemas)
- [x] quickstart.md (setup and demo guide)
- [x] research.md (performance/protocol notes)
- [ ] specs/001-handwash-compliance/tasks.md (to be generated by `/speckit.tasks`)
