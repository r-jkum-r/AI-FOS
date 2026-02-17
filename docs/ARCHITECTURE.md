# System Architecture

## Overview

Production-grade multilingual AI voice translation system enabling real-time bidirectional communication between Field Officers (regional languages) and IT Teams (Hinglish).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         TELEPHONY LAYER                          │
│  FOS Phone Call (PSTN/SIP) ──→ Asterisk PBX ──→ RTP Stream     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      GATEWAY LAYER                               │
│  FastAPI Backend + WebSocket Handler + Redis State Manager      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AI PROCESSING PIPELINE                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Whisper  │→→ │ fastText │→→ │ NLLB-200 │→→ │ Coqui    │    │
│  │   STT    │   │ Lang Det │   │Translator│   │   TTS    │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                                │
│  Synthesized Audio ──→ RTP Stream ──→ IT Team SIP Call         │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Telephony Layer (Asterisk)
- SIP/PJSIP server handling incoming calls
- RTP audio streaming
- ARI (Asterisk REST Interface) for call control
- External media support for WebSocket audio

### 2. Gateway Layer (FastAPI)
- WebSocket server for real-time audio streaming
- Call lifecycle management
- Session state in Redis
- Load balancing across multiple instances

### 3. AI Pipeline
- **Whisper STT**: Streaming speech recognition
- **fastText**: Language detection (Tamil/Telugu/Kannada/Marathi/Hindi)
- **NLLB-200**: Multilingual translation
- **Coqui TTS**: Voice synthesis in target language

### 4. Data Flow

**FOS → IT Team:**
1. FOS speaks Tamil
2. Audio → Whisper → "வணக்கம்"
3. fastText detects Tamil
4. NLLB translates → "Namaste"
5. Coqui TTS → Hinglish voice
6. Audio → IT Team

**IT Team → FOS:**
1. IT speaks Hinglish
2. Audio → Whisper → "How can I help?"
3. NLLB translates → Tamil text
4. Coqui TTS → Tamil voice
5. Audio → FOS

## Scalability

- Horizontal scaling via Kubernetes HPA
- Redis for distributed state
- Stateless backend instances
- Load balancer for SIP traffic

## Performance Targets

- Latency: <3 seconds end-to-end
- Throughput: 1000+ concurrent calls
- Availability: 99.9%
