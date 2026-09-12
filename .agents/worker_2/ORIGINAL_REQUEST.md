## 2026-07-23T03:56:19Z
You are worker_2 in C:\Users\megat\Hermes-WebApp\.agents\worker_2.
Your task is to implement Requirement R2: Voice Command Terminal & STEM Audio Stream for Hermes-WebApp in C:\Users\megat\Hermes-WebApp.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Key steps to execute:
1. Backend Service: Create `backend/services/audio_engine.py` with `AudioEngine` class implementing audio frame VAD (Voice Activity Detection), STEM demux frequency filter processing (Vocals, Drums, Bass, Other), and Voice CLI command intent parser mapping speech commands to system actions.
2. Backend Router: Create `backend/routers/audio.py` with REST endpoints `GET /api/audio/status` and `POST /api/audio/process-stem`.
3. Backend WebSocket: Create `backend/websockets/audio.py` for `/ws/audio` supporting binary PCM audio frame streaming and JSON command frames, returning real-time speech transcripts, matched CLI commands, and stem spectrum telemetry.
4. Register `audio.router` and `/ws/audio` endpoint in `backend/main.py`.
5. Frontend UI: Edit `static/index.html` adhering strictly to Anti-AI Slop OLED dark aesthetic (`#000` dark background, `.glass` cards, Bento-box grid):
   - Add `#voice-toggle-badge` in `<header>` with mic status toggle and input indicator.
   - Add `#mod-audio` full-screen module overlay (Dock item index 7 with mic icon) featuring WebAudio multi-stem frequency spectrum visualizer canvas (`#stem-audio-canvas`), real-time speech transcript box, voice command auto-execute toggle, and controls.
   - Add frontend JS for `getUserMedia` recording, binary `/ws/audio` streaming, and STEM canvas visualizer.
6. Unit Tests: Create `tests/test_audio_api.py` covering REST endpoints and `/ws/audio` WebSocket connection.
7. Run `pytest -v tests/test_audio_api.py` to verify implementation.
8. Write detailed handoff report to `C:\Users\megat\Hermes-WebApp\.agents\worker_2\handoff.md` including exact commands executed and passing test logs.
9. Send completion message to parent.
