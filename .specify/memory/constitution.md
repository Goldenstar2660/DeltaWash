<!--
Sync Impact Report
- Version change: 0.0.0 -> 1.0.0 (initial ratification)
- Modified principles: N/A (all principles newly defined)
- Added sections: Core Principles, System Scope & Constraints, Delivery Workflow & Compliance, Governance
- Removed sections: None
- Templates requiring updates:
	- OK .specify/templates/plan-template.md (constitution gates referenced generically; no edits needed)
	- OK .specify/templates/spec-template.md (user-story and requirement structure already compliant)
	- OK .specify/templates/tasks-template.md (task grouping by user story remains valid)
- Follow-up TODOs: None
-->

# DeltaWash Pi CV Constitution

## Core Principles

### Spec-Driven Scope Discipline
Specs, approved plans, and task lists are the only sources of truth. Every code change must reference a governing spec section, and tests must trace back to the same artifact. Prefer minimal shippable implementation; no speculative features or future-proofing without spec. No cloud services, user accounts, touchscreens, or extra sensors may be introduced without a ratified spec update. Detection coverage remains limited to WHO hand-rubbing steps 2-7, and new step requests require a major revision. 

### Modular On-Device Architecture
All computation runs locally on Raspberry Pi 5 (4 GB) with the Pi Camera Module 3 using Python, MediaPipe Hands for landmarks, and OpenCV for preprocessing. Each WHO step is implemented as an independent detector module that exposes a shared detector interface that outputs step confidence + any signals needed for the interpreter (timing handled centrally). A state-machine/event interpreter consumes detector events, manages per-step timers, and emits feedback signals. Feedback (ESP8266 LED driver) and logging layers interact with the interpreter via interfaces so they can evolve without touching detection logic. Configured timing thresholds, completion criteria, and LED rules live in validated config files, not hardcoded, and reloading configs must not require detector rewrites.

### Real-Time Reliability & Fail-Safe Operation
Maintain stable real-time performance on Pi 5; any optimization must prefer predictable FPS over marginal accuracy gains. The system must prioritize "uncertain" states over false completion and keep reporting partial progress until confidence recovers. Camera disconnects, sensor warm-ups, or MediaPipe stalls must fail safe and log recoverable errors. WiFi failures while notifying the ESP8266 must never crash detection; degrade gracefully.

### Observability & Analytics
Emit structured logs (session_id, timestamp, config_version, detector_id, step_status, confidence, duration_ms, errors) to per-session records stored locally. Aggregate analytics (most-missed step, average completion times, timeouts, uncertainty frequency) must be recomputed incrementally and exportable as CSV/JSON when requested. Every record must reference the config hash to guarantee traceability between behavior and thresholds. All runs must record config hash; config changes must be reviewed like code.

### Verification, Privacy & Demo Readiness
This project is permanently **demo-only**. Unit tests cover detector signal logic using recorded or synthetic landmark sequences, while integration tests validate state-machine progression, timing accumulation, and ESP8266 messaging. A smoke-test script exercises the live camera + MediaPipe pipeline. All fixtures must be reproducible and stored with metadata. Privacy still forbids cloud services, identity recognition, or linking sessions to people, but persisted media (e.g., demo recordings) may be written whenever operators explicitly enable them; manual enable/disable plus manual deletion is sufficient. No automated retention limits, deletion policies, warning banners, or audit logging are required. A deterministic demo mode replays curated landmark/video samples, drives console/overlay step status, and powers hackathon-ready quickstart instructions. Demo recordings are non-normative artifacts: they are excluded from compliance guarantees, analytics, and correctness requirements, and they do not trigger audit or policy enforcement.

## System Scope & Constraints

- Platform: Raspberry Pi 5 (4 GB) with Pi Camera Module 3, Python runtime, MediaPipe Hands, and OpenCV; no cloud or external compute.
- Detection scope: WHO steps 2-7 only, completed in any order; each step tracks accumulated dwell time that must meet configurable minimums before completion is asserted.
- Configuration: Timing thresholds, detector sensitivity, uncertainty tolerances, and LED rules load from a validated config file (e.g., YAML/JSON) whose schema is versioned; invalid configs refuse to boot.
- Feedback: After detectors reach reliability targets, interpreter events publish via WiFi to an ESP8266 LED controller (per-step LED turns solid when complete, optional blink for current step). Network outages degrade gracefully without blocking detection.
- Logging & analytics: Maintain rolling per-session files plus lifetime aggregates summarizing misses, averages, and failure patterns (including optional uncertainty flags) for compliance reviews; demo recordings remain separate and optional.

## Delivery Workflow & Compliance

- Every feature begins with a constitution-aligned spec; plans/tasks inherit the same principle gates before work starts.
- Implementation must keep detector modules, interpreter/state machine, feedback drivers, and logging separated into separate modules/layers with clear interfaces and folder boundaries; avoid unnecessary packaging until needed.
- Timing thresholds or completion criteria changes occur through config updates plus validation tests; never direct code edits.
- Pull requests require: detector unit tests (recorded/synthetic sequences), state-machine integration tests, ESP8266 comm tests or stubs, camera smoke-test script results, and demo-mode regression proof.
- Quickstart docs must include deterministic demo instructions, sample logs, and visible step-status output (console overlay or textual grid) for hackathon readiness.

## Governance

- This constitution supersedes other process docs for the DeltaWash Pi CV project. Reviews block merges that violate any principle.
- Amendment process: propose change referencing affected sections, provide impact analysis, and update specs/tasks to preserve traceability. Minor textual clarifications bump PATCH versions; adding/removing principles or redefining governance bumps MINOR or MAJOR respectively.
- Compliance reviews occur at each milestone (plan approval, pre-demo, release). Each review must cite structured logs plus config hashes to prove adherence.
- Incident handling: failures such as camera disconnects, timing misconfigurations, or network outages trigger root-cause notes linked to the session logs and tracked until resolved.
- Demo recordings are intentionally treated as non-normative, manually managed artifacts per the relaxed privacy principle ratified in version 1.1.0.

**Version**: 1.1.0 | **Ratified**: 2026-01-10 | **Last Amended**: 2026-01-10
