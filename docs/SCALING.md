# Scaling Strategy

## Horizontal Scaling

### Backend Instances
```bash
# Scale to 10 replicas
kubectl scale deployment backend --replicas=10 -n voice-agent

# Auto-scaling based on CPU/Memory
kubectl autoscale deployment backend \
  --min=3 --max=20 \
  --cpu-percent=70 \
  -n voice-agent
```

### Asterisk Instances
- Deploy multiple Asterisk instances behind SIP load balancer
- Use DNS SRV records for SIP routing
- Session affinity via Redis

## Performance Optimization

### 1. Model Optimization
```python
# Use quantized models
whisper_model = WhisperModel("medium", compute_type="int8")

# Batch processing where possible
translations = await translator.translate_batch(texts, src, tgt)
```

### 2. Caching Strategy
```python
# Cache translations in Redis
cache_key = f"trans:{hash(text)}:{src}:{tgt}"
cached = await redis.get(cache_key)
if cached:
    return cached
```

### 3. GPU Acceleration
```yaml
# Kubernetes GPU node
resources:
  limits:
    nvidia.com/gpu: 1
```

## Load Testing

```bash
# Simulate 1000 concurrent calls
artillery quick --count 1000 --num 10 http://localhost:8000/api/call/initiate
```

## Monitoring Metrics

- Active calls per instance
- Average latency per pipeline stage
- GPU utilization
- Memory usage
- Error rates

## Cost Optimization

- Use spot instances for non-critical workloads
- Auto-scale down during off-peak hours
- Model quantization (int8/int4)
- Batch inference where possible
