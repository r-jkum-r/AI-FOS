"""
Prometheus metrics for monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
import time

# Metrics
calls_total = Counter('voice_agent_calls_total', 'Total number of calls', ['status'])
call_duration = Histogram('voice_agent_call_duration_seconds', 'Call duration')
active_calls = Gauge('voice_agent_active_calls', 'Number of active calls')
translation_latency = Histogram('voice_agent_translation_latency_seconds', 'Translation latency', ['stage'])
errors_total = Counter('voice_agent_errors_total', 'Total errors', ['type'])

async def metrics_endpoint():
    """Expose metrics for Prometheus"""
    return Response(content=generate_latest(), media_type="text/plain")

class MetricsMiddleware:
    """Middleware to track request metrics"""
    
    async def __call__(self, request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            calls_total.labels(status='success').inc()
            return response
        except Exception as e:
            calls_total.labels(status='error').inc()
            errors_total.labels(type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time
            call_duration.observe(duration)
