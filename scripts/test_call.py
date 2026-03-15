"""
Local dev test client — simulates a phone call without real telephony.

Usage:
    python scripts/test_call.py --audio path/to/audio.wav
    python scripts/test_call.py --text "வணக்கம் எப்படி இருக்கீங்க"
    python scripts/test_call.py --generate tamil

Requires:
    pip install websockets soundfile numpy scipy
"""
import argparse
import asyncio
import io
import sys
import uuid
import wave

import numpy as np


API_URL = "http://localhost:8000"
WS_URL  = "ws://localhost:8000"


# ── Helpers ───────────────────────────────────────────────────────────────────

def pcm_from_wav(path: str) -> bytes:
    with wave.open(path, "rb") as wf:
        assert wf.getsampwidth() == 2, "WAV must be 16-bit PCM"
        return wf.readframes(wf.getnframes())


def generate_test_audio(duration_sec: float = 3.0, sample_rate: int = 16000) -> bytes:
    """Generate a sine-wave tone as 16-bit PCM (simulates speech for pipeline testing)."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    tone = (np.sin(2 * np.pi * 440 * t) * 0.3 * 32767).astype(np.int16)
    return tone.tobytes()


def text_to_pcm(text: str, sample_rate: int = 16000) -> bytes:
    """
    Synthesise speech from text using gTTS (if available) or fall back to tone.
    Install gTTS: pip install gTTS pydub
    """
    try:
        from gtts import gTTS
        import tempfile, os
        import soundfile as sf

        tts = gTTS(text=text, lang="ta")  # Tamil — change lang as needed
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_mp3 = f.name
        tts.save(tmp_mp3)

        # Convert mp3 → wav PCM via ffmpeg
        tmp_wav = tmp_mp3.replace(".mp3", ".wav")
        os.system(f"ffmpeg -y -i {tmp_mp3} -ar {sample_rate} -ac 1 -f s16le {tmp_wav} -loglevel quiet")
        with open(tmp_wav, "rb") as f:
            pcm = f.read()
        os.unlink(tmp_mp3)
        os.unlink(tmp_wav)
        return pcm
    except ImportError:
        print("gTTS not installed — using tone instead. pip install gTTS to use text input.")
        return generate_test_audio()


# ── WebSocket test call ───────────────────────────────────────────────────────

async def wait_for_models(timeout: int = 300):
    """Poll /ready until models are loaded or timeout."""
    import httpx
    print("Waiting for AI models to load", end="", flush=True)
    async with httpx.AsyncClient() as client:
        for _ in range(timeout):
            try:
                r = await client.get(f"{API_URL}/ready", timeout=3)
                if r.status_code == 200:
                    print(" ready.")
                    return True
            except Exception:
                pass
            print(".", end="", flush=True)
            await asyncio.sleep(1)
    print("\nTimed out waiting for models.")
    return False


async def run_test_call(audio_bytes: bytes, call_id: str):
    try:
        import websockets
    except ImportError:
        print("ERROR: websockets not installed. Run: pip install websockets")
        sys.exit(1)

    uri = f"{WS_URL}/ws/audio/{call_id}"
    print(f"\n{'='*50}")
    print(f"  Call ID : {call_id}")
    print(f"  Endpoint: {uri}")
    print(f"  Audio   : {len(audio_bytes)} bytes ({len(audio_bytes)//32000:.1f}s @ 16kHz)")
    print(f"{'='*50}\n")

    chunk_size = 3200  # 100ms of 16kHz 16-bit mono audio
    received_chunks = []

    async with websockets.connect(uri) as ws:
        print("Connected. Streaming audio...")

        # Send audio in chunks (simulates real-time streaming)
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i:i + chunk_size]
            await ws.send(chunk)
            await asyncio.sleep(0.1)  # 100ms pacing

            # Check for any response audio
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=0.05)
                if isinstance(response, bytes):
                    received_chunks.append(response)
                    print(f"  ← Received {len(response)} bytes of translated audio")
            except asyncio.TimeoutError:
                pass

        print("\nAudio stream complete. Waiting for pipeline to finish...")
        print("(STT + translation + TTS typically takes 3-10s per chunk)")
        wait = 30
        for i in range(wait):
            await asyncio.sleep(1)
            print(f"\r  Waiting... {i+1}/{wait}s", end="", flush=True)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=0.1)
                if isinstance(response, bytes):
                    received_chunks.append(response)
                    print(f"\n  ← Received {len(response)} bytes of translated audio")
            except asyncio.TimeoutError:
                pass
        print()

        # Drain any remaining responses
        while True:
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                if isinstance(response, bytes):
                    received_chunks.append(response)
                    print(f"  ← Received {len(response)} bytes of translated audio")
            except asyncio.TimeoutError:
                break

    # Save output audio if any received
    if received_chunks:
        output_path = f"output_{call_id[:8]}.raw"
        with open(output_path, "wb") as f:
            for chunk in received_chunks:
                f.write(chunk)
        total = sum(len(c) for c in received_chunks)
        print(f"\nSaved {total} bytes of output audio to {output_path}")
        print(f"Play with: ffplay -f s16le -ar 22050 -ac 1 {output_path}")
    else:
        print("\nNo translated audio received yet.")
        print("Check backend logs: docker compose logs backend --tail=30")

    print(f"\nCall transcript: {API_URL}/api/call/{call_id}/transcript")
    print(f"Call status    : {API_URL}/api/call/{call_id}/status")


# ── Health check ─────────────────────────────────────────────────────────────

async def check_health():
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{API_URL}/health", timeout=5)
            data = r.json()
            print(f"Backend: {data['status']} (v{data['version']})")

            r2 = await client.get(f"{API_URL}/health/detailed", timeout=5)
            checks = r2.json().get("checks", {})
            for svc, status in checks.items():
                icon = "✓" if status == "healthy" else "✗"
                print(f"  {icon} {svc}: {status}")
        return True
    except Exception as e:
        print(f"Backend not reachable: {e}")
        print("Make sure docker compose is running: docker compose up -d")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Voice Agent local test client")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--audio", help="Path to a 16-bit mono 16kHz WAV file")
    group.add_argument("--text",  help="Text to synthesise and send (requires gTTS)")
    group.add_argument("--generate", metavar="LANG",
                       help="Generate a test tone (any value, e.g. tamil)")
    parser.add_argument("--call-id", default=None, help="Custom call ID (default: random UUID)")
    args = parser.parse_args()

    print("\n Voice Agent — Local Test Client")
    print("=" * 50)

    healthy = await check_health()
    if not healthy:
        sys.exit(1)

    # Wait for AI models to finish loading before sending audio
    models_ready = await wait_for_models(timeout=300)
    if not models_ready:
        print("Models did not load in time. Check: docker compose logs backend -f")
        sys.exit(1)

    call_id = args.call_id or str(uuid.uuid4())

    if args.audio:
        print(f"\nLoading WAV: {args.audio}")
        audio = pcm_from_wav(args.audio)
    elif args.text:
        print(f"\nSynthesising: {args.text!r}")
        audio = text_to_pcm(args.text)
    else:
        lang = args.generate or "tamil"
        print(f"\nGenerating test tone (simulating {lang} speech)...")
        audio = generate_test_audio(duration_sec=3.0)

    await run_test_call(audio, call_id)


if __name__ == "__main__":
    asyncio.run(main())
