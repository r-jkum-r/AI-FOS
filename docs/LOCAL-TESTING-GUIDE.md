# Local Dev Testing Guide

Test the full voice translation pipeline locally — no phone, no SIP trunk, no real calls needed.

---

## Prerequisites

- Docker Desktop running
- Python 3.11+ (for the test client script)
- ffmpeg installed locally (for audio conversion)

Install ffmpeg if you don't have it:
```bash
# Ubuntu/WSL
sudo apt-get install ffmpeg

# Windows (via winget)
winget install ffmpeg

# Mac
brew install ffmpeg
```

Install test client dependencies:
```bash
pip install websockets httpx numpy soundfile
```

---

## 1. Start the Stack

```bash
docker compose up -d --build
```

Wait about 2 minutes on first run — models download during build.

Verify everything is healthy:
```bash
docker compose ps
```

Expected:
```
NAME            STATUS
freeswitch-1    running (healthy)
redis-1         running (healthy)
backend-1       running (healthy)
prometheus-1    running
grafana-1       running
jaeger-1        running
```

If backend is not healthy yet, wait and check:
```bash
docker compose logs backend --tail=20
```

You should see:
```
Redis connected
Call handler and stream manager initialised
FreeSWITCH ESL task started
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

---

## 2. Confirm the API is Up

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status": "healthy", "service": "voice-gateway", "version": "2.0.0"}
```

```bash
curl http://localhost:8000/health/detailed
```

Expected:
```json
{
  "status": "operational",
  "checks": {
    "redis": "healthy",
    "esl": "healthy",
    "kafka": "unavailable"
  }
}
```

Kafka unavailable is fine — it is not in the local stack.

---

## 3. Run a Test Call

Open a second terminal to watch logs while you test:
```bash
docker compose logs backend -f
```

### Option A — Tone test (no audio file needed)

Quickest way to verify the pipeline is wired end to end:

```bash
python scripts/test_call.py --generate tamil
```

This sends a synthetic audio tone through the full chain:
WebSocket → STT → language detect → translate → TTS → response audio

---

### Option B — Real WAV file

If you have a recording of someone speaking Tamil/Telugu/Hindi:

First convert it to the required format (16-bit, mono, 16kHz):
```bash
ffmpeg -i your_recording.mp3 -ar 16000 -ac 1 -sample_fmt s16 test.wav
```

Then send it:
```bash
python scripts/test_call.py --audio test.wav
```

---

### Option C — Text input (synthesises speech first)

Install gTTS:
```bash
pip install gTTS
```

Then run with any regional language text:
```bash
# Tamil
python scripts/test_call.py --text "சில நேரங்களில் அதிக போக்குவரத்து, வன்பொருள் செயலிழப்பு அல்லது மென்பொருள் பிழைகள் காரணமாக ஒரு சேவையகம்"

# Telugu
python scripts/test_call.py --text "నమస్కారం మీరు ఎలా ఉన్నారు"

# Hindi
python scripts/test_call.py --text "नमस्ते आप कैसे हैं"

# Kannada
python scripts/test_call.py --text "ನಮಸ್ಕಾರ ನೀವು ಹೇಗಿದ್ದೀರಿ"
```

---

## 4. What to Expect in the Logs

First call will be slow (30-60 seconds) — Whisper and NLLB load into memory.
Subsequent calls on the same container are fast.

```
[<call-id>] Pipeline started
[<call-id>] STT model loaded
[<call-id>] Language detector loaded
[<call-id>] Translation model loaded
[<call-id>] TTS model loaded
[<call-id>] STT: 'வணக்கம்'
[<call-id>] Detected: tamil
[<call-id>] Translated: 'Namaste'
[<call-id>] Sent 44100 bytes of TTS audio
```

---

## 5. Check the Call Record

Replace `<call-id>` with the ID printed by the test script.

```bash
# Call info
curl http://localhost:8000/api/call/<call-id>/status

# Transcript
curl http://localhost:8000/api/call/<call-id>/transcript

# All active calls
curl http://localhost:8000/calls
```

---

## 6. Play the Output Audio

The test script saves translated audio to a `.raw` file in the current directory.

```bash
# Linux/WSL
ffplay -f s16le -ar 22050 -ac 1 output_<call-id>.raw

# Convert to WAV for any player
ffmpeg -f s16le -ar 22050 -ac 1 -i output_<call-id>.raw output.wav
```

---

## 7. View Dashboards

| Dashboard   | URL                        | Credentials  |
|-------------|----------------------------|--------------|
| Grafana     | http://localhost:3000      | admin / admin |
| Prometheus  | http://localhost:9090      | —            |
| Jaeger      | http://localhost:16686     | —            |
| API Docs    | http://localhost:8000/docs | —            |
| Raw Metrics | http://localhost:8000/metrics | —         |

In Grafana, check these metrics after a test call:
- `voice_calls_total` — call counts by status
- `stt_latency_seconds` — transcription time
- `translation_latency_seconds` — translation time
- `tts_latency_seconds` — synthesis time
- `audio_packets_total` — packets processed
- `voice_active_calls` — currently active calls

---

## 8. Test the REST API Directly

You can also drive the system without audio using the API:

```bash
# Create a call manually
curl -X POST "http://localhost:8000/api/call/initiate?caller_number=9876543210&destination=it-team"

# Set source language
curl -X POST "http://localhost:8000/calls/<call-id>/language?language=tamil"

# Get call status
curl http://localhost:8000/api/call/<call-id>/status

# Terminate call
curl -X POST "http://localhost:8000/api/call/<call-id>/hangup"
```

Or use the interactive Swagger UI at http://localhost:8000/docs — every endpoint is there with a Try it out button.

---

## 9. Troubleshooting

**Backend not starting:**
```bash
docker compose logs backend --tail=50
```

**Models not loading (out of memory):**
The AI models need ~8GB RAM total. Check Docker Desktop memory allocation:
Settings → Resources → Memory → set to at least 10GB

**STT returns empty string:**
The tone generator produces a sine wave, not real speech — Whisper's VAD filter will correctly detect no speech. Use `--audio` or `--text` for real transcription testing.

**ESL connection errors in logs:**
Expected — FreeSWITCH mock is running but the backend retries with exponential backoff. Not an error for local testing.

**Port already in use:**
```bash
docker compose down
docker compose up -d
```

**Full reset:**
```bash
docker compose down -v
docker compose build --no-cache backend
docker compose up -d
```

---

## 10. Supported Languages

| Language | Code (NLLB) | Test phrase |
|----------|-------------|-------------|
| Tamil    | tam_Taml    | வணக்கம் |
| Telugu   | tel_Telu    | నమస్కారం |
| Kannada  | kan_Knda    | ನಮಸ್ಕಾರ |
| Marathi  | mar_Deva    | नमस्कार |
| Hindi    | hin_Deva    | नमस्ते |

All translate to Hinglish (hin_Deva) by default.
Change `TARGET_LANGUAGE` in `.env` to translate to a different language.

---

## Next Step

Once local testing works, see `docs/DEPLOYMENT.md` for deploying to a cloud VM with a real SIP trunk and phone number.
