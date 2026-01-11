---
description: "Task list for implementing on-device WHO Steps 2-7 compliance"
---

# Tasks: On-Device WHO Steps 2-7 Compliance

**Input**: Design documents from `/specs/001-handwash-compliance/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1-US6)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the Python project, dependencies, baseline assets, and lock remaining spec ambiguities before building feature code.

- [x] T001 Create the src/deltawash_pi package tree (detectors/, interpreter/, feedback/, logging/, config/, demo/, cli/) with placeholder `__init__.py` files starting at src/deltawash_pi/__init__.py.
- [x] T002 Declare runtime dependencies (mediapipe, opencv-python, numpy, requests, onnxruntime) and Python 3.11 metadata in requirements.txt.
- [x] T003 [P] Configure pytest defaults (pytest.ini) and create empty test packages under tests/unit, tests/integration, and tests/smoke/ with `__init__.py` stubs.
- [x] T004 [P] Add baseline operator assets (config/example.yaml with ROI/motion placeholders including `relative_motion_threshold`, model block with path/fallback settings, 3000 ms defaults for steps 2-7, optional `demo_recording`/`video_capture` blocks, and demos/README.md describing curated dataset expectations).
- [x] T005 [P] Review specs/001-handwash-compliance/spec.md to confirm the console text grid format and 1 Hz LED blink pattern remain aligned with plan.md; only update the spec if future drift is discovered.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared infrastructure (config, datatypes, CLI skeleton, demo assets, dataset annotations, guardrails) that every user story depends on.

- [x] T006 Implement schema-validated config loader + error messaging in src/deltawash_pi/config/loader.py covering ROI, motion thresholds (including `relative_motion_threshold`), step thresholds, ESP8266 block, model block (path, format, fallback_allowed, confidence thresholds, window settings), optional `demo_recording.enabled/output_path`, and optional `video_capture` storage + retention fields (disabled by default).
- [x] T007 [P] Define shared dataclasses/enums (FramePacket, StepSignal, ModelInferenceResult, FallbackEvent, SessionRecord stubs) in src/deltawash_pi/interpreter/types.py referencing specs/001-handwash-compliance/data-model.md so shared types stay within the documented package structure.
- [x] T008 [P] Stub CLI entrypoints (capture.py, demo.py, analytics.py, led_test.py, smoke_camera.py, roi_calibrate.py) with argparse wiring and config loading in src/deltawash_pi/cli/.
- [x] T009 [P] Create deterministic demo asset manifest (demos/manifest.json) and loader scaffolding in src/deltawash_pi/demo/replay.py that emits FramePacket streams.
- [x] T010 Document initial MediaPipe FPS benchmark + ROI guidance findings in specs/001-handwash-compliance/research.md using the smoke camera CLI output.
- [x] T011 [P] Define and document a minimally labeled subset of the 30-session dataset (update demos/manifest.json and demos/README.md with per-step annotations) to support accuracy scoring.
- [x] T012 Implement a repeatable latency benchmark in src/deltawash_pi/cli/smoke_camera.py (and tests/smoke/test_latency.py) that measures capture→detector processing, enforces the <200 ms target, and fails when the threshold is exceeded.

**Checkpoint**: Core infrastructure ready; user story work can start.

---

## Phase 3: User Story 1 - Session Auto-Start/Stop (Priority: P1) (MVP)

**Goal**: Automatically open/close sessions when exactly two hands enter/exit the configurable ROI with sustained rubbing motion.

**Independent Test**: Replay labeled sink footage and verify session start/end timestamps align with ROI presence + motion thresholds, with no false positives.

### Implementation

- [x] T013 [US1] Implement ROI + motion gating logic with two-hand verification, absolute and relative motion thresholds, and timeouts in src/deltawash_pi/interpreter/session_manager.py.
- [x] T014 [US1] Wire session gating into the capture pipeline by emitting lifecycle events from src/deltawash_pi/cli/capture.py once FramePacket streams meet thresholds.
- [x] T015 [US1] Build ROI calibration overlay + live preview command in src/deltawash_pi/cli/roi_calibrate.py so operators can tune coordinates before capture.
- [x] T016 [US1] Add unit tests covering start-window, stop-timeout, and false-positive rejection cases (including relative motion threshold failures) in tests/unit/test_session_manager.py using synthetic motion traces.
- [x] T017 [US1] Ensure the capture CLI ignores raw frames by default and, when `demo_recording.enabled` is true, writes a sequence of annotated output frames (images) under `demo_recording.output_path`; when `video_capture.enabled` is true, write capture artifacts to `video_capture.storage_path` and apply retention only if configured.
- [x] T018 [US1] Add a demo/video recording smoke test in tests/smoke/test_demo_recording.py proving (a) default sessions leave no annotated frames or capture artifacts behind, (b) enabling demo recording creates the expected annotated frame set at the configured path, and (c) enabling video capture respects retention limits when configured.

**Checkpoint**: Session lifecycle is reliable and independently testable.

---

## Phase 4: User Story 2 - WHO Step Recognition (Priority: P2)

**Goal**: Classify WHO Steps 2-7 using a pre-trained landmark-sequence classifier with heuristic fallback; emit orientation metadata and confidence scores.

**Independent Test**: Feed canonical landmark sequences (including orientation variants) and confirm the classifier outputs the correct `StepSignal` values with expected confidence; verify fallback to heuristics when model confidence is low.

### Implementation

- [x] T019 [US2] Implement detector base class with shared configuration + confidence gating in src/deltawash_pi/detectors/base.py and register modules in src/deltawash_pi/detectors/__init__.py.
- [x] T020 [P] [US2] Build individual heuristic detectors (src/deltawash_pi/detectors/step2.py ... step7.py) that compute geometric cues and orientation for each canonical step (used as fallback).
- [x] T021 [US2] Add a detector runner that the interpreter polls each frame (src/deltawash_pi/detectors/runner.py) to aggregate `StepSignal` outputs per FramePacket.
- [x] T022 [US2] Create detector unit tests + fixtures in tests/unit/test_detectors.py leveraging demos fixtures for confident vs. uncertain scenarios.

**Checkpoint**: Detectors emit per-step signals independently of timing logic.

---

## Phase 5: User Story 3 - Per-Step Timing & Completion (Priority: P3)

**Goal**: Accumulate confident dwell time per step from model or heuristic signals, pause/resume on uncertainty, and mark completion once thresholds are met (steps may finish out of order).

**Independent Test**: Run scripted StepSignal sequences (from both model and heuristic sources) to ensure timing resumes after uncertainty, thresholds toggle completion exactly once, and totals persist at session end.

### Implementation

- [x] T023 [US3] Implement interpreter state machine with per-step timers, uncertainty halts, and completion events in src/deltawash_pi/interpreter/state_machine.py.
- [x] T024 [US3] Add timing accumulator unit tests (pause/resume, multi-step, uncertain resets) in tests/unit/test_timing.py.
- [x] T025 [US3] Integrate interpreter outputs with session manager events in src/deltawash_pi/cli/capture.py to reset on session boundaries and stream `step_state_update` events.
- [x] T026 [US3] Create integration test that feeds scripted detector outputs through interpreter/session manager in tests/integration/test_interpreter.py (covers out-of-order completions).

**Checkpoint**: Timing + completion logic works end-to-end with synthetic signals.

---

## Phase 6: User Story 4 - Demo-Friendly Progress Reporting (Priority: P4)

**Goal**: Provide real-time status output (text grid or similar) that highlights current step and mirrors interpreter changes within 500 ms, plus deterministic demo mode replay.

**Independent Test**: Use demo mode to replay a known sequence and confirm status output chronology and formatting match logged events with deterministic results.

- [x] T027 [US4] Implement console status reporter showing per-step state + accumulated ms with active-step highlight in src/deltawash_pi/feedback/status.py (matches spec's console grid decision).
- [x] T028 [US4] Hook the status reporter into live capture (src/deltawash_pi/cli/capture.py) and demo CLI rendering (src/deltawash_pi/cli/demo.py) with refresh throttling.
- [x] T029 [US4] Complete deterministic demo replay pipeline in src/deltawash_pi/demo/replay.py + src/deltawash_pi/cli/demo.py, including invariant checks and optional ground-truth comparison.
- [x] T030 [US4] Add smoke test covering demo replay + status output in tests/smoke/test_demo_mode.py with recorded fixtures.
- [x] T031 [US4] Extend the demo/status smoke test (tests/smoke/test_demo_mode.py) to measure status refresh latency and fail when updates exceed the 500 ms budget.

**Checkpoint**: Demo observers can track progress without reading logs.

---

## Phase 7: User Story 5 - Structured Logging & Aggregation (Priority: P5)

**Goal**: Persist per-session JSONL logs with SessionRecord fields (including model usage metrics and fallback events) and provide analytics summarizing most-missed steps, averages, uncertainty frequencies, and model performance.

**Independent Test**: Run multiple synthetic sessions, inspect generated logs for required fields including model_version and fallback_events, and execute analytics CLI to verify computed aggregates including model_usage_rate.

- [x] T032 [US5] Implement JSONL session logger capturing SessionRecord + uncertainty events + fallback events in src/deltawash_pi/logging/sessions.py.
- [x] T033 [US5] Build aggregation pipeline + CLI command (src/deltawash_pi/logging/aggregates.py and src/deltawash_pi/cli/analytics.py) to compute metrics defined in data-model.md including model_usage_rate and avg_model_confidence.
- [x] T034 [US5] Wire session logger + uncertainty events + fallback events into capture workflow in src/deltawash_pi/cli/capture.py, ensuring config_version, model_version, and roi_rect are recorded.
- [x] T035 [US5] Add analytics integration test using sample logs in tests/integration/test_analytics.py to verify aggregates including model metrics.
- [x] T036 [US5] Implement an accuracy evaluation path in src/deltawash_pi/cli/analytics.py that consumes the labeled demo subset/logs to compute WHO step completion accuracy (SC-001) and fails the command when accuracy falls below 85%.
- [x] T037 [US5] Persist and report the computed accuracy metric inside logs/aggregates/summary.json (and CLI output) so stakeholders can track compliance trends.

**Checkpoint**: Logs + analytics provide actionable session insights.

---

## Phase 8: User Story 6 - Optional ESP8266 LED Feedback (Priority: P6)

**Goal**: Publish step completion events to an ESP8266 over HTTP without blocking the detection loop; unreachable endpoints log warnings and auto-disable LEDs for the session.

**Independent Test**: Use a stub or actual ESP8266 to verify step completion toggles LEDs within 500 ms when reachable and the system continues normally when disconnected.

- [x] T038 [US6] Implement synchronous HTTP LED client with 500 ms timeout + warning/disable behavior in src/deltawash_pi/feedback/esp8266.py per contracts/interfaces.md, emitting `CURRENT`/`COMPLETED`/`IDLE` states and the spec-defined 1 Hz blink mode for the current step.
- [x] T039 [US6] Bridge interpreter step state events to the LED client inside src/deltawash_pi/interpreter/state_machine.py (emit `CURRENT` on active step changes, `COMPLETED` on threshold hit, and `IDLE` on reset when enabled).
- [x] T040 [US6] Implement CLI LED test utility that triggers arbitrary step/state payloads (`CURRENT`/`COMPLETED`/`IDLE`) in src/deltawash_pi/cli/led_test.py and logs failures.
- [x] T041 [US6] Add LED smoke test with HTTP stub covering success + unreachable cases in tests/smoke/test_led_client.py.
- [x] T045 [US6] Add SC-004-focused smoke test in tests/smoke/test_led_client.py that drives a local HTTP stub, measures publish latency from request send to response receipt, and fails when elapsed time exceeds 500 ms.

**Checkpoint**: LED feedback is optional, resilient, and isolated from critical path.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation, cleanup, and verification across user stories.

- [x] T042 [P] Update specs/001-handwash-compliance/quickstart.md and troubleshooting steps to reflect the implemented CLIs, privacy defaults, and LED guidance.
- [x] T043 [P] Reconcile data-model.md and contracts/interfaces.md with actual payloads (threshold defaults, LedSignal states, demo recording metadata) after implementation.
- [x] T044 Run full smoke + demo suite (tests/smoke/, cli capture/demo commands, latency benchmark, model inference benchmark, accuracy check) and record known issues + follow-ups in specs/001-handwash-compliance/plan.md.

---

## Explicit Out-of-Scope (NOT Tasks for This Repository)

The following activities are performed externally and are NOT implementation tasks:

- **Data labeling**: Annotating landmark sequences with ground-truth WHO step labels
- **Model training**: Training, fine-tuning, or retraining the landmark-sequence classifier
- **Hyperparameter tuning**: Architecture search, learning rate optimization, augmentation strategies
- **Training infrastructure**: GPU clusters, experiment tracking, model versioning pipelines
- **Dataset curation**: Collecting, cleaning, and balancing training datasets
- **Model export/conversion**: Converting trained models to ONNX or TFLite format
- **Medical validation**: Clinical trials, regulatory compliance, or medical-grade certification
- **End-to-end vision models**: Image-based CNNs that bypass MediaPipe landmarks
- **On-device training**: Any form of online learning or model adaptation on the Raspberry Pi

This repository ONLY:
1. Loads a pre-trained model file as an input artifact
2. Validates the model file format and shape
3. Runs inference using the model
4. Falls back to heuristics when model is unavailable or low confidence
5. Logs model usage metrics for observability

---

## Dependencies & Execution Order

- **Setup (Phase 1)** must finish before Foundational work begins.
- **Foundational (Phase 2)** blocks all user stories; once complete, User Stories 1-6 can proceed (prefer priority order for MVP).
- **User Story Dependencies**:
  - US1 must complete before US3-US6 (interpreters, logging, LEDs) because they rely on session events.
  - US2 feeds US3+; detectors and ML classifier must exist before timing, reporting, logging, or LEDs integrate signals.
  - US2 ML model tasks (T046-T052) can run in parallel with heuristic detector polish (T020-T022) once shared types are stable.
  - US4 depends on US3 (status output uses interpreter states).
  - US5 depends on US1-US3 for accurate data but can evolve alongside US4.
  - US6 depends on US3 outputs but is optional after MVP.
- **Model file artifact**: The pre-trained model file (ONNX/TFLite) is an external input; system runs without it if `model.fallback_allowed=true`.
- **Polish (Phase 9)** runs after desired user stories are complete.

## Parallel Opportunities

- Setup tasks T001-T004 can be split among team members (different files).
- During Foundational phase, T006-T009 involve separate modules and can run concurrently once T006 is defined.
- Once Foundational completes:
  - US1 and US2 can begin in parallel (session manager vs. detectors) so long as shared types are stable.
  - Within US2, detector implementations for steps 2-7 (T020) can be divided per file.
  - Later stories (US4-US6) can overlap after their dependencies finish, e.g., analytics (US5) in parallel with LED work (US6).

## Parallel Example: User Story 2 (WHO Step Recognition)

```bash
# Heuristic detectors (fallback path):
Task: "T020 [P] [US2] Build per-step heuristic detectors (src/deltawash_pi/detectors/step2.py ... step7.py)"
Task: "T021 [US2] Add a detector runner ... src/deltawash_pi/detectors/runner.py"
Task: "T022 [US2] Create detector unit tests ... tests/unit/test_detectors.py"

# ML model integration (can run in parallel after T019):
Task: "T046 [US2] Implement model loader ... src/deltawash_pi/detectors/model_loader.py"
Task: "T047 [US2] Implement LandmarkSequenceClassifier ... src/deltawash_pi/detectors/sequence_classifier.py"
Task: "T048 [US2] Integrate classifier into DetectorRunner ... src/deltawash_pi/detectors/runner.py"

# Tests (after implementation tasks):
Task: "T049-T052 [US2] Model and fallback tests"
```

## Implementation Strategy

### MVP First

1. Complete Phases 1-2 to establish infrastructure.
2. Deliver User Story 1 (session auto-start/stop) for the minimal viable demo.
3. Add User Story 2 (detectors) and User Story 3 (timing) to achieve full compliance detection.
4. Pause for validation before proceeding.

### Incremental Delivery

- After MVP (US1-3), add US4 (status + demo) for demo readiness.
- Layer US5 (logging/analytics) to provide audit trails.
- Finish with US6 (LED feedback) only if hardware is available.

### Team Parallelization

- One engineer can focus on session manager/interpreter (US1 + US3) while another owns detectors (US2).
- A third contributor can prepare logging + analytics (US5) once interpreter outputs are stable.
- ESP8266 work (US6) remains isolated and can start after US3 completes, even if other stories continue.
