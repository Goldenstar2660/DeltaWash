# Research Notes: DeltaWash Pi WHO Steps 2-7

## Vision Pipeline Considerations
- **MediaPipe Hands**: Runs at ~30 FPS on Pi 5 when using 640x480 frames; we target 24 FPS to leave CPU for interpreter/logging.
- **OpenCV ROI**: Pre-cropping frames to the configured ROI reduces pixels processed and improves hand detection stability.
- **Lighting**: Consistent overhead lighting minimizes reflective noise; consider diffusers near sinks.

## ML Model Architecture Considerations

### Model Type Selection
- **Landmark-sequence classifier (recommended)**: Temporal 1D CNN or TCN operating on MediaPipe landmark sequences. Reuses existing landmark extraction, lightweight, and fits Pi 5 CPU budget.
- **Crop-based CNN (not recommended)**: Image classifier on hand crops. Requires far more labeled data, GPU training, and borderline Pi 5 inference without accelerators.
- **Hybrid boosted model (marginal gains)**: Gradient boosting on handcrafted features. Easy to implement but accuracy ceiling limited by feature engineering.

### Model Input Specification
- **Input shape**: `[batch, window_frames, landmarks]`
  - `window_frames`: 16-24 frames (~0.5-1.0 s at 24 FPS)
  - `landmarks`: 42 values (2 hands × 21 keypoints × 1 distance-normalized 2D) or 126 values (2 hands × 21 × 3D)
- **Normalization**: Wrist-centered, scale-normalized by wrist-to-MCP9 distance, hand-ordered (left before right)
- **Padding**: Incomplete windows padded with zeros or last valid frame

### Model Output Specification
- **Output shape**: `[batch, 7]` with softmax probabilities for:
  - `NONE`, `STEP_2`, `STEP_3`, `STEP_4`, `STEP_5`, `STEP_6`, `STEP_7`
- **Orientation**: Derived from landmark asymmetry or separate output head for steps 3, 6, 7

### Training Data Requirements (External)
- **Target dataset**: ~30-40 sessions × 6 steps × multiple volunteers = >10,000 labeled windows
- **Augmentation**: Temporal jitter, mirroring (left/right swap), landmark noise injection
- **Labeling**: Per-frame or per-window ground-truth step annotations
- **Note**: Training is performed offline on external infrastructure; this repository only consumes the trained model

## Performance Targets
- **Latency budget**: Max 200 ms end-to-end per frame (capture -> landmarks -> detectors -> interpreter -> status).
- **Model inference budget**: Max 5 ms per window on Pi 5 CPU (single Cortex-A76 core).
- **Model loading budget**: Max 2 seconds at startup for model loading + validation.
- **Monitoring**: Capture FPS via moving average; log warnings if FPS < 20 over 5 seconds.
- **Camera disconnect handling**: Use OpenCV capture health checks; on failure, emit `uncertainty_event` and attempt reconnect without killing process.

### Model Inference Benchmarks (Target)
- **Architecture**: 1D CNN with 2-3 temporal convolution blocks, ~50K-200K parameters
- **Input window**: 16 frames × 42 landmarks = 672 floats per inference
- **Expected latency**: 2-5 ms on Cortex-A76 with ONNX Runtime CPU
- **Memory footprint**: <10 MB model file, <50 MB runtime memory

### ONNX Runtime Configuration
- **Execution provider**: CPU only (no CUDA, no CoreML)
- **Thread count**: 1-2 threads to avoid starving MediaPipe
- **Graph optimization**: Enable basic optimizations at session creation
- **Quantization**: INT8 quantization optional for further speedup (requires calibration dataset)

### Smoke Camera Benchmark (2026-01-10)
- Command: `python -m deltawash_pi.cli.smoke_camera --config config/example.yaml --frames 200`
- Hardware: Raspberry Pi 5 (4 GB), Pi Camera Module 3, 640×480 capture, ROI `x=120,y=80,w=400,h=360`.
- Results: mean FPS 27.6, mean capture→detector latency 162 ms, p95 latency 188 ms (comfortably within the <200 ms target).
- ROI guidance: shrinking ROI width below 360 px reduced false positives but cost ~3 FPS due to extra camera motion; keeping width at 400 px maintains full hand coverage while preserving FPS. Height above 360 px produced diminishing returns and larger background glare regions.
- Follow-up: bake the measured latency thresholds into the smoke CLI so regressions fail CI once detector integration lands.
- **Model inference**: Not yet benchmarked; expected <5 ms overhead per window based on architecture analysis.

### Model Format Considerations

| Format | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| ONNX | Wide runtime support, good Pi 5 performance, easy export from PyTorch/TF | Slightly larger file size | **Primary choice** |
| TFLite | Excellent mobile optimization, smaller files | Requires tflite_runtime, fewer optimizations on ARM64 | Secondary option |
| PyTorch | Direct Python integration | Heavy runtime, slow startup, large memory | Not recommended |

**Decision**: Use ONNX as primary format with onnxruntime. TFLite supported as fallback via optional tflite_runtime dependency.

## ESP8266 Protocol Choice
- **HTTP POST rationale**: Simplest stack (no MQTT broker), human-debuggable via curl, tolerant of stateless calls; adequate for hackathon reliability.
- **Timeout**: 500 ms per POST; failures logged, no retry to avoid blocking detection loop.

## Dataset Needs
- **Demo Asset**: 30-session curated dataset covering all step variants, annotated with start/end times for each step.
- **Unit-Test Fixtures**: `.npz` files storing landmark sequences for each step to drive detector tests.
- **Uncertainty Scenarios**: Recordings with multiple hands or reflective noise to validate fail-safe behavior.
- **Model Validation Dataset**: Held-out labeled sequences for computing accuracy metrics (SC-001 target: 85%).
- **Fallback Test Cases**: Sequences with low MediaPipe confidence or ambiguous poses to validate heuristic fallback behavior.

## Model Artifact Management

### Model File Location
- **Default path**: `models/step_classifier.onnx` (relative to project root)
- **Config override**: `model.path` in config file allows custom location
- **Version tracking**: Model file hash stored in SessionRecord for reproducibility

### Model Versioning (External Concern)
- Model training produces versioned artifacts with:
  - Training dataset hash
  - Architecture description
  - Validation accuracy metrics
- This repository does not manage model versions; it loads whatever file is specified in config

### Fallback Behavior
- **Model missing + fallback_allowed=true**: Log warning, run heuristic-only mode
- **Model missing + fallback_allowed=false**: Refuse to start, exit with error
- **Model invalid (wrong shape)**: Same as missing
- **Model loads but inference fails**: Log error, fall back to heuristics for that window
- **Low model confidence**: Fall back to heuristics, log fallback_event
