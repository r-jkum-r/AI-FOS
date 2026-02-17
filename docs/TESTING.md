# Testing Guide

## SIP Softphone Testing

### 1. Install SIP Client

Recommended clients:
- Linphone (cross-platform)
- Zoiper (Windows/Mac/Linux)
- MicroSIP (Windows)

### 2. Configure SIP Account

```
Domain: <your-asterisk-ip>:5060
Username: fos-trunk
Password: (as configured)
Transport: UDP
```

### 3. Make Test Call

1. Dial extension configured in Asterisk
2. Speak in regional language (Tamil/Telugu/etc.)
3. Verify Hinglish audio output
4. Test bidirectional conversation

## API Testing

### Health Check

```bash
curl http://localhost:8000/health
```

### Initiate Call

```bash
curl -X POST http://localhost:8000/api/call/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "caller_number": "+919876543210",
    "destination": "it-team"
  }'
```

### Check Call Status

```bash
curl http://localhost:8000/api/call/{call_id}/status
```

## Load Testing

### Using Artillery

```bash
npm install -g artillery

# Create test scenario
cat > load-test.yml <<EOF
config:
  target: "http://localhost:8000"
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Call initiation"
    flow:
      - post:
          url: "/api/call/initiate"
          json:
            caller_number: "+919876543210"
            destination: "it-team"
EOF

# Run test
artillery run load-test.yml
```

## Audio Quality Testing

### 1. Record Test Audio

```bash
# Record 10 seconds of Tamil speech
ffmpeg -f alsa -i default -t 10 -ar 16000 test_tamil.wav
```

### 2. Send to Pipeline

```python
import asyncio
import websockets
import wave

async def test_audio():
    uri = "ws://localhost:8000/ws/audio/test-call-123"
    
    async with websockets.connect(uri) as ws:
        with wave.open("test_tamil.wav", "rb") as wf:
            data = wf.readframes(1024)
            while data:
                await ws.send(data)
                response = await ws.recv()
                print(f"Received {len(response)} bytes")
                data = wf.readframes(1024)

asyncio.run(test_audio())
```

### 3. Verify Output

- Check transcription accuracy
- Measure latency (should be <3s)
- Verify translation quality
- Test voice clarity

## Language Detection Testing

```python
from backend.language_detector import LanguageDetector

detector = LanguageDetector()

test_cases = [
    ("வணக்கம், எப்படி இருக்கீங்க?", "tamil"),
    ("నమస్కారం, మీరు ఎలా ఉన్నారు?", "telugu"),
    ("ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?", "kannada"),
    ("नमस्कार, तुम्ही कसे आहात?", "marathi"),
    ("नमस्ते, आप कैसे हैं?", "hindi")
]

for text, expected in test_cases:
    detected = await detector.detect(text)
    assert detected == expected, f"Failed: {text}"
    print(f"✓ {expected} detected correctly")
```

## Performance Benchmarks

Target metrics:
- End-to-end latency: <3 seconds
- Concurrent calls: 1000+
- CPU usage: <70% at peak
- Memory: <8GB per instance
- Audio quality: MOS >4.0

## Monitoring Tests

```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# Check active calls
curl http://localhost:8000/stats
```
