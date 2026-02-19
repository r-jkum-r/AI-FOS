# Quick Reference - Corporate WSL Setup

## 🚀 Quick Start (Your Environment)

```bash
# 1. Open WSL Ubuntu terminal
# 2. Navigate to project
cd ~/AI-FOS

# 3. Start Docker (if not running)
sudo service docker start

# 4. Start all services
docker-compose up -d

# 5. Wait 2-3 minutes, then check health
curl http://localhost:8000/health
```

## 📋 Daily Commands

### Start Your Day
```bash
# Start Docker
sudo service docker start

# Start services
cd ~/AI-FOS
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

### Check Status
```bash
# All services
docker-compose ps

# View logs
docker-compose logs -f backend

# Check stats
curl http://localhost:8000/stats
```

### End Your Day (Optional)
```bash
# Stop services to save resources
docker-compose down

# Or leave running for faster restart tomorrow
```

## 🌐 Access URLs (From Windows Browser)

```
API Documentation:  http://localhost:8000/docs
Health Check:       http://localhost:8000/health
Statistics:         http://localhost:8000/stats
Grafana Dashboard:  http://localhost:3000 (admin/admin)
Prometheus:         http://localhost:9090
```

## 🔧 Common Issues & Quick Fixes

### Docker Not Running
```bash
sudo service docker start
```

### Services Not Starting
```bash
# Check logs
docker-compose logs backend

# Restart
docker-compose restart
```

### Out of Memory
```bash
# Use smaller model in .env
WHISPER_MODEL_SIZE=small
MAX_CONCURRENT_CALLS=5

# Restart
docker-compose restart backend
```

### After VPN Reconnect
```bash
# Restart Docker
sudo service docker restart

# Restart services
docker-compose restart
```

### Slow Performance
```bash
# Check resources
docker stats

# Check WSL memory (in Windows PowerShell)
wsl --list --verbose
```

## 🔍 Troubleshooting Commands

```bash
# Check Docker
sudo service docker status

# Check containers
docker-compose ps

# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs asterisk

# Check disk space
df -h

# Check memory
free -h

# Check ports
sudo netstat -tulpn | grep -E ':(8000|5060|6379)'
```

## 📊 Monitoring

### Check System Health
```bash
# Backend health
curl http://localhost:8000/health

# System stats
curl http://localhost:8000/stats

# Docker stats
docker stats --no-stream
```

### View Metrics
```bash
# Open in browser
http://localhost:3000  # Grafana
http://localhost:9090  # Prometheus
```

## 🔐 Corporate Network Issues

### Proxy Issues
```bash
# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Test connection
curl -I https://google.com
```

### SSL Certificate Issues
```bash
# Check certificates
ls /usr/local/share/ca-certificates/

# Update certificates
sudo update-ca-certificates
```

### Firewall Issues
```bash
# Check if ports are blocked
telnet localhost 8000
telnet localhost 5060
```

## 🛠️ Maintenance

### Update System
```bash
# Update Ubuntu
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

### Clean Up
```bash
# Remove unused Docker resources
docker system prune -a

# Clean Ubuntu
sudo apt clean
sudo apt autoremove
```

### Backup Configuration
```bash
# Backup .env file
cp .env .env.backup

# Backup models (after first run)
docker run --rm -v ai-fos_ai-models:/data -v $(pwd):/backup ubuntu tar czf /backup/models-backup.tar.gz /data
```

## 📞 Test API

### Initiate Test Call
```bash
curl -X POST "http://localhost:8000/api/call/initiate?caller_number=1234567890&destination=9876543210"
```

### Check Call Status
```bash
curl http://localhost:8000/api/call/{call_id}/status
```

### Get Transcript
```bash
curl http://localhost:8000/api/call/{call_id}/transcript
```

## 🆘 Emergency Commands

### Everything Broken? Reset!
```bash
# Stop everything
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Restart Docker
sudo service docker restart

# Start fresh
docker-compose up -d
```

### Still Not Working?
```bash
# Check detailed logs
docker-compose logs --tail=100

# Run verification
bash scripts/verify-setup.sh

# Check system resources
free -h
df -h
docker stats
```

## 📚 Documentation Quick Links

- **Full Setup**: [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md)
- **General Guide**: [QUICKSTART.md](QUICKSTART.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Troubleshooting**: [FIX-SSL-ISSUES.md](FIX-SSL-ISSUES.md)

## 💡 Pro Tips

1. **Keep Docker Running**: Leave services running between sessions for faster startup
2. **Use Smaller Models**: Set `WHISPER_MODEL_SIZE=small` in .env for better performance
3. **Monitor Resources**: Check `docker stats` if system feels slow
4. **Bookmark URLs**: Save http://localhost:8000/docs for quick access
5. **Check Logs First**: Always run `docker-compose logs backend` when troubleshooting

## 🎯 Performance Tuning for Corporate Laptop

```bash
# Edit .env for optimal corporate laptop performance
nano .env

# Recommended settings:
WHISPER_MODEL_SIZE=small          # Faster, less memory
MAX_CONCURRENT_CALLS=10           # Reasonable for laptop
CORS_ORIGINS=http://localhost:*   # Local only
```

## 🔄 After Windows Restart

```bash
# WSL might need restart
wsl --shutdown  # In Windows PowerShell
# Then reopen WSL Ubuntu

# Start Docker
sudo service docker start

# Start services
cd ~/AI-FOS
docker-compose up -d
```

## ✅ Health Check Checklist

- [ ] Docker running: `sudo service docker status`
- [ ] Containers up: `docker-compose ps`
- [ ] Backend healthy: `curl http://localhost:8000/health`
- [ ] No errors in logs: `docker-compose logs --tail=50`
- [ ] Ports accessible: `netstat -tulpn | grep 8000`

---

**Need Help?** Check [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) for detailed troubleshooting.
