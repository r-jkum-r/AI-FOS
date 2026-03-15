"""
Prometheus metrics - single source of truth.
All counters/histograms/gauges used across the application.
"""
from prometheus_client import Counter, Histogram, Gauge

calls_total = Counter('voice_calls_total', 'Total calls processed', ['status'])
call_duration = Histogram('voice_call_duration_seconds', 'Call duration in seconds')
active_calls = Gauge('voice_active_calls', 'Number of active calls')
audio_packets_processed = Counter('audio_packets_total', 'Audio packets processed')
translation_latency = Histogram('translation_latency_seconds', 'Translation latency in seconds')
stt_latency = Histogram('stt_latency_seconds', 'STT latency in seconds')
tts_latency = Histogram('tts_latency_seconds', 'TTS latency in seconds')
errors_total = Counter('voice_errors_total', 'Total errors', ['type'])
