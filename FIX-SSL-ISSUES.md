# Fix Docker SSL Certificate Issues

## Problem
You're getting: `tls: failed to verify certificate: x509: certificate signed by unknown authority`

This happens when:
- Behind corporate proxy/firewall
- Corporate SSL inspection is enabled
- Docker can't verify SSL certificates

## Quick Fixes (Try in Order)

### Fix 1: Update CA Certificates (Recommended)

```bash
# Update system certificates
sudo apt update
sudo apt install ca-certificates -y
sudo update-ca-certificates

# Restart Docker
sudo service docker restart

# Try again
docker-compose build --no-cache
```

### Fix 2: Configure Docker to Use System Certificates

```bash
# Create Docker daemon config
sudo mkdir -p /etc/docker

# Add certificate configuration
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "insecure-registries": [],
  "registry-mirrors": []
}
EOF

# Restart Docker
sudo service docker restart

# Try again
docker-compose build --no-cache
```

### Fix 3: Use Docker Hub Mirror (If Behind Firewall)

```bash
# Edit docker-compose.yml to use pre-built images instead of building
# Or pull images manually first

# Pull base images manually
docker pull python:3.11-slim
docker pull redis:7-alpine
docker pull andrius/asterisk:18
docker pull prom/prometheus:latest
docker pull grafana/grafana:latest

# Then build
docker-compose build --no-cache
```

### Fix 4: Disable SSL Verification (Temporary - Not Recommended)

```bash
# Add to /etc/docker/daemon.json
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "insecure-registries": ["docker.io"],
  "disable-legacy-registry": false
}
EOF

# Restart Docker
sudo service docker restart
```

### Fix 5: Configure Corporate Proxy

If you're behind a corporate proxy:

```bash
# Set proxy environment variables
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1"

# Configure Docker to use proxy
sudo mkdir -p /etc/systemd/system/docker.service.d

sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=http://proxy.company.com:8080"
Environment="HTTPS_PROXY=http://proxy.company.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

# Reload and restart
sudo systemctl daemon-reload
sudo service docker restart
```

### Fix 6: Install Corporate Root Certificate

If your company uses SSL inspection:

```bash
# Get the corporate root certificate from IT
# Save it as corporate-cert.crt

# Install the certificate
sudo cp corporate-cert.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Restart Docker
sudo service docker restart
```

## Alternative: Use Pre-Built Images

Instead of building, use pre-built images from Docker Hub:

### Option A: Simplified docker-compose.yml

Create a new file `docker-compose.simple.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes

  backend:
    image: tiangolo/uvicorn-gunicorn-fastapi:python3.11
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  asterisk:
    image: andrius/asterisk:18
    ports:
      - "5060:5060/udp"
      - "8088:8088"
    volumes:
      - ./asterisk:/etc/asterisk
```

Then run:
```bash
docker-compose -f docker-compose.simple.yml up -d
```

### Option B: Manual Installation (No Docker)

If Docker continues to have issues, install directly on WSL:

```bash
# Install Python and dependencies
sudo apt update
sudo apt install -y python3.11 python3-pip redis-server

# Install Python packages
cd backend
pip3 install -r ../requirements.txt

# Start Redis
sudo service redis-server start

# Start backend
python3 main.py
```

## Verify Fix

After applying any fix:

```bash
# Test Docker connectivity
docker pull hello-world

# If successful, try building again
cd ~/AI-FOS
docker-compose build --no-cache
docker-compose up -d
```

## Still Having Issues?

### Check Network Connectivity

```bash
# Test DNS
nslookup docker.io

# Test connectivity
curl -I https://registry-1.docker.io/v2/

# Check proxy settings
env | grep -i proxy
```

### Check Docker Status

```bash
# Check Docker is running
sudo service docker status

# Check Docker logs
sudo journalctl -u docker --no-pager | tail -50

# Check Docker info
docker info
```

### WSL-Specific: Reset Docker

```bash
# Stop Docker
sudo service docker stop

# Remove Docker data (WARNING: deletes all containers/images)
sudo rm -rf /var/lib/docker

# Start Docker
sudo service docker start

# Try again
docker-compose build --no-cache
```

## Recommended Solution for Corporate Networks

1. **Contact IT Department** - Get corporate root certificate
2. **Install certificate** - Follow Fix 6 above
3. **Configure proxy** - Follow Fix 5 if needed
4. **Use mirror** - Ask IT for approved Docker registry mirror

## Quick Workaround (For Testing)

Use the simplified compose file without building:

```bash
# Create minimal setup
cat > docker-compose.minimal.yml <<EOF
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  backend:
    image: python:3.11-slim
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    working_dir: /app
    command: bash -c "pip install fastapi uvicorn redis && uvicorn main:app --host 0.0.0.0"
EOF

docker-compose -f docker-compose.minimal.yml up -d
```

This avoids the build step entirely.
