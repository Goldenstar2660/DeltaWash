# Quickstart: DeltaWash Pi WHO Steps 2-7 Demo

## 1. Hardware Setup
- Raspberry Pi 5 (4 GB) with Raspberry Pi OS Bookworm.
- Pi Camera Module 3 mounted above sink at ~45 deg angle, USB power to Pi.
- Optional: ESP8266 with 6 LEDs (Steps 2-7) + WiFi access.

## 2. Software Prerequisites
```bash
sudo apt update && sudo apt install -y python3-venv python3-opencv python3-picamera2 libcamera-apps python3-pytest
python3 -m venv --system-site-packages .venv && source .venv/bin/activate
pip install -e .
pip install -r requirements.txt  # mediapipe, opencv-python, numpy, onnxruntime, requests
```
> Tip: rerun `source .venv/bin/activate` in every new shell before invoking CLIs.

## 2.5. Model File Setup (Required for ML-based Classification)

The system uses a pre-trained landmark-sequence classifier for WHO step detection. The model file is trained offline and provided as a deployment artifact.

### Obtaining the Model File
1. **From your ML team**: Request the latest `step_classifier.onnx` file trained on your labeled dataset.
2. **Place in models directory**:
```bash
mkdir -p models
cp /path/to/step_classifier.onnx models/step_classifier.onnx
```

### Model Configuration
Edit `config/local.yaml` to specify model settings:
```yaml
model:
  enabled: true                          # Enable ML-based classification
  path: "models/step_classifier.onnx"    # Path to model file
  format: "onnx"                         # Model format: "onnx" or "tflite"
  fallback_allowed: true                 # Run heuristics if model unavailable
  model_confidence_min: 0.6              # Minimum model confidence to use
  landmark_confidence_min: 0.5           # Minimum MediaPipe confidence
  window_frames: 16                      # Frames per classification window
  window_stride: 8                       # Overlap between windows
```

### Running Without a Model (Heuristic-Only Mode)
If you don't have a trained model yet, set:
```yaml
model:
  enabled: true
  fallback_allowed: true  # System will run using heuristic detectors only
```
The system will log a warning at startup and operate in heuristic-only mode.

### Strict Model Requirement
For production deployments requiring ML classification, set:
```yaml
model:
  enabled: true
  fallback_allowed: false  # System will refuse to start without valid model, onnxruntime
```

## 3. Configure ROI & Thresholds
1. Copy `config/example.yaml` to `config/local.yaml`.
2. Edit ROI coordinates to match your camera framing.
3. Adjust per-step `duration_ms` and `confidence_min` if needed.
4. Leave `esp8266.enabled=false` until the ESP8266 responds to ping/curl. When ready, update `esp8266.host` (e.g., `http://192.168.4.50`) and run the LED test CLI (see §7) before live capture.
5. (Optional) Enable `video_capture.enabled` to record demo video; set `retention_seconds` or `max_sessions` and an absolute `storage_path`.
6. (Optional) Use the live ROI overlay (requires Picamera2 + display):
```bash
python -m deltawash_pi.cli.roi_calibrate --config config/local.yaml --write-back
```
   For headless tuning, add `--headless` with `--dx/--dy/--dw/--dh`. For X11 forwarding, reduce display load with `--preview-scale 0.5`. If the camera is upside down, add `--rotate-180` (or `--hflip/--vflip`).
7. (Optional) Tune hand tracking robustness in `hand_tracking` (lower confidences and smoothing reduce dropouts but may add false positives).
8. (Optional) Adjust session gating: `session.min_hands` (default 2) and `session.require_motion` (default true).

## 4. Run Live Pipeline
```bash
python -m deltawash_pi.cli.capture --config config/local.yaml
```
- Console status grid mirrors interpreter updates (<500 ms latency budget).
- Session logs land in `logs/sessions/YYYY-MM-DD.jsonl`; purge old files before demos to keep accuracy reports clean.
- Optional flags:
  - `--preview`, `--preview-scale`, `--rotate-180`, `--hflip`, `--vflip` for camera alignment.
  - `--demo-asset sample-sequence` to replay fixtures instead of Pi camera input.
  - `--mock-session --mock-frames 60` for deterministic testing without MediaPipe.
  - `--log-steps` to print the most confident detector output at `--log-steps-interval` cadence.

## 5. Run Deterministic Demo Mode
```bash
python -m deltawash_pi.cli.demo --config config/example.yaml --asset sample-sequence --verify
```
- Streams curated asset(s) through detectors/interpreter and asserts annotations via `--verify`.
- Combine with `--manifest demos/manifest.json` to target a specific manifest when running custom datasets.
- Use when validating new heuristics, LED wiring (with esp8266 enabled), or analytics accuracy without touching the live sink.

## 6. Aggregated Analytics
```bash
python -m deltawash_pi.cli.analytics summarize --logs logs/sessions --out logs/aggregates/summary.json
python -m deltawash_pi.cli.analytics accuracy --manifest demos/manifest.json --logs logs/sessions --out logs/aggregates/summary.json --threshold 0.85
```
- `summarize` refreshes stats_version, most-missed step, latency, uncertainty, fallback metrics.
- `accuracy` enforces SC-001 (85% completion accuracy) against labeled demo sessions. It only considers logs where `demo_mode=true` and `demo_asset_id` matches the manifest; prune stale logs if the tool cannot find demo runs.

## 7. ESP8266 LED Test (Optional)
```bash
python -m deltawash_pi.cli.led_test --config config/local.yaml --step STEP_5 --state COMPLETED
```
- Requires `esp8266.enabled=true` and a reachable host; fails fast (<=500 ms) and reports disable reason on stderr when unreachable.
- States: `CURRENT` (1 Hz blink handled on firmware), `COMPLETED` (solid), `IDLE` (LED off). Use before demos so capture sessions do not attempt to auto-discover LEDs mid-run.

## 8. Smoke Test Script
```bash
# Mock mode (CI/headless validation)
python -m deltawash_pi.cli.smoke_camera --config config/local.yaml --frames 200 --mock

# Hardware mode (Pi camera attached)
python -m deltawash_pi.cli.smoke_camera --config config/local.yaml --frames 200
```
- Enforces the <200 ms latency budget by failing when `mean` or `p95` exceed the threshold. Run before capture sessions to catch camera regressions.

## 9. Troubleshooting
- **Camera not detected**: run `libcamera-hello` to verify hardware, reboot Pi.
- **OpenCV capture**: not supported in smoke test; Picamera2 is the only backend.
- **High preview latency**: X11 forwarding adds delay; use a local display or try `--preview-scale 0.5`.
- **Upside-down camera**: run `python -m deltawash_pi.cli.roi_calibrate --rotate-180 ...` to align the preview.
- **Hand detection dropouts**: reduce `hand_tracking.min_detection_confidence`, `min_tracking_confidence`, and increase `smoothing_window`.
- **Session doesn't start**: lower `session.min_hands` or set `session.require_motion=false` for testing.
- **Low FPS**: disable LED integration, reduce frame size (e.g., 640x480), ensure throttling is off.
- **ESP8266 offline**: leave `esp8266.enabled=false` or point `host` to `http://127.0.0.1` for local stub testing; the LED client auto-disables for the session after the first failure.
- **LEDs out of sync / stuck blinking**: rerun `python -m deltawash_pi.cli.led_test --state IDLE` for the affected step, or power-cycle the ESP8266; the Pi never retries mid-session once a timeout occurs.
- **ROI mismatch**: use `python -m deltawash_pi.cli.roi_calibrate --write-back` (Picamera2 capture + OpenCV display) or `--headless` without a display.

### Model-Related Issues
- **"Model file not found" at startup**: Verify `model.path` points to a valid `.onnx` or `.tflite` file. If you don't have a model, set `model.fallback_allowed=true`.
- **"Model validation failed" at startup**: The model file may be corrupt or have incorrect input/output shapes. Check the model was exported correctly (expected input: `[batch, 16, 42]` or similar).
- **"Falling back to heuristics" warnings**: Model confidence is below `model.model_confidence_min`. This is normal during ambiguous poses; increase threshold for stricter model usage or lower it for more model reliance.
- **High model inference latency**: Check that onnxruntime is using CPU provider correctly. Ensure no GPU provider is accidentally enabled. Consider quantizing the model to INT8.
- **System refuses to start**: If `model.fallback_allowed=false` and model is missing/invalid, the system will exit. Either fix the model or set `fallback_allowed=true`.
- **Accuracy CLI says no demo sessions**: delete stale files under `logs/sessions/`, re-run capture in `--demo-asset <id>` mode to regenerate demo-mode logs, then rerun `analytics accuracy`.
- **Low accuracy with model**: Verify the model was trained on data matching your camera setup, lighting, and hand positioning. Check `logs/aggregates/summary.json` for `accuracy.value`, `model_usage_rate`, and per-asset breakdowns.
