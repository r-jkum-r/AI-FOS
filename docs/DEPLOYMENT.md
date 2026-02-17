# Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (for production)
- 8GB+ RAM per backend instance
- GPU recommended (NVIDIA with CUDA support)

## Local Development

```bash
# Clone repository
git clone <repo-url>
cd voice-ai-agent

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Test health
curl http://localhost:8000/health
```

## Production Deployment (Kubernetes)

### 1. Build and Push Images

```bash
# Build backend image
docker build -t your-registry/voice-agent-backend:latest -f infra/dockerfile .

# Push to registry
docker push your-registry/voice-agent-backend:latest
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace voice-agent

# Apply configurations
kubectl apply -f infra/kubernetes/

# Check status
kubectl get pods -n voice-agent
kubectl get svc -n voice-agent
```

### 3. Configure Asterisk SIP

Update `asterisk/sip.conf` with your public IP:

```ini
external_media_address=YOUR_PUBLIC_IP
external_signaling_address=YOUR_PUBLIC_IP
```

### 4. Scale Backend

```bash
# Manual scaling
kubectl scale deployment backend --replicas=10 -n voice-agent

# Auto-scaling is configured via HPA (3-20 replicas)
kubectl get hpa -n voice-agent
```

## Environment Variables

```bash
# Backend
REDIS_URL=redis://redis:6379
ASTERISK_ARI_URL=http://asterisk:8088/ari
ASTERISK_ARI_USER=asterisk
ASTERISK_ARI_PASSWORD=asterisk

# Optional: GPU acceleration
CUDA_VISIBLE_DEVICES=0
```

## Monitoring

Access dashboards:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## Security Hardening

1. Change default Asterisk credentials
2. Enable TLS for SIP (PJSIP TLS transport)
3. Use Redis password authentication
4. Configure firewall rules for SIP/RTP ports
5. Enable rate limiting on API endpoints

## Troubleshooting

```bash
# Check backend logs
kubectl logs -f deployment/backend -n voice-agent

# Check Asterisk status
kubectl exec -it deployment/asterisk -n voice-agent -- asterisk -rx "core show channels"

# Test Redis connection
kubectl exec -it deployment/redis -n voice-agent -- redis-cli ping
```
