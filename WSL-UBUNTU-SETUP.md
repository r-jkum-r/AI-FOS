# 🎤 Voice Agent - WSL Ubuntu Setup Guide

## Quick Start (5 Minutes)

### Step 1: Ensure WSL2 is Running

```powershell
# In Windows PowerShell (as Administrator)
wsl --install Ubuntu-22.04
wsl --set-version Ubuntu-22.04 2
```

### Step 2: Clone/Access Project in WSL

```bash
# In WSL Ubuntu terminal
cd /mnt/c/Users/raj.kumar.in/Desktop/AI-FOS

# Or copy to WSL home for better performance
cp -r /mnt/c/Users/raj.kumar.in/Desktop/AI-FOS ~/AI-FOS
cd ~/AI-FOS
```

### Step 3: Run Setup Script

```bash
# Make script executable
chmod +x scripts/wsl-setup.sh

# Run setup (installs Docker, builds project, starts services)
bash scripts/wsl-setup.sh
```

### Step 4: Access Dashboard

Once setup completes, open your browser:
- **FastAPI API**: http://localhost:8000
- **Grafana Dashboard**: http://localhost:3000
- **Jaeger Tracing**: http://localhost:16686

---

## Detailed Setup Instructions

### Prerequisites

**Windows Side:**
- Windows 10/11 (Build 19041 or later)
- WSL2 enabled
- 8GB RAM minimum (16GB recommended)
- 20GB disk space

**Setup Time:**
- First run: 15-20 minutes (includes Docker build)
- Subsequent runs: 2-3 minutes

### Install WSL2

#### Option A: Automatic (Windows 11)

```powershell
# Open PowerShell as Administrator
wsl --install

# Restart your computer when prompted
```

#### Option B: Manual (Windows 10/11)

```powershell
# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Enable WSL
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Download and install WSL2 kernel
# https://aka.ms/wsl2kernel

# Restart computer
# Then set WSL2 as default
wsl --set-default-version 2
```

#### Install Ubuntu Distribution

```powershell
# From Microsoft Store or command line
wsl --install -d Ubuntu-22.04

# Or list available distributions
wsl --list --online
```

---

### Windows Configuration for WSL

Create/edit `%USERPROFILE%\.wslconfig` (Windows file, not in WSL):

```ini
[wsl2]
memory=8GB
processors=4
swap=4GB
localhostForwarding=true

[interop]
enabled=true
appendWindowsPath=true
```

Save file, then restart WSL:

```powershell
wsl --shutdown
```

---

### Start WSL Terminal

**Option A: From PowerShell**
```powershell
wsl
```

**Option B: From Windows Terminal**
- Install Windows Terminal from Microsoft Store
- Select "Ubuntu" from dropdown

**Option C: File Explorer**
- Right-click in folder → "Open in Terminal"

---

### Access Project from Windows

#### Method 1: Via Network Path

From Windows File Explorer or terminal:
```
\\wsl$\Ubuntu-22.04\home\<username>\AI-FOS
```

#### Method 2: Via /mnt

From within WSL, Windows C: drive is accessible:
```bash
cd /mnt/c/Users/raj.kumar.in/Desktop/AI-FOS
```

**Performance Note:** For better Docker performance, copy the project to WSL home directory:
```bash
cp -r /mnt/c/... ~/AI-FOS
cd ~/AI-FOS
```

---

## Automated Setup

### Using the Setup Script

```bash
# Navigate to project
cd ~/AI-FOS

# Make setup script executable
chmod +x scripts/wsl-setup.sh

# Run setup (fully automated)
bash scripts/wsl-setup.sh
```

The script will:
1. ✅ Check WSL environment
2. ✅ Install system dependencies
3. ✅ Install Docker & Docker Compose
4. ✅ Configure WSL optimizations
5. ✅ Build Docker images
6. ✅ Start all services
7. ✅ Verify services are healthy
8. ✅ Display access information

---

## Manual Setup

If you prefer manual setup or the script fails:

### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Docker

```bash
# Remove old Docker versions
sudo apt remove -y docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Verify installation
docker --version
```

### Step 3: Install Docker Compose

```bash
# Download latest release
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker-compose --version
```

### Step 4: Configure Docker

```bash
# Add current user to docker group (no sudo needed)
sudo usermod -aG docker $USER

# Apply group changes (choose one)
newgrp docker
# OR log out and log back in

# Test Docker (should work without sudo)
docker ps
```

### Step 5: Install Python & Dependencies

```bash
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential
```

### Step 6: Build & Start Project

```bash
cd ~/AI-FOS

# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

---

## Verify Installation

### Check Docker

```bash
docker --version
docker ps
docker images
```

### Check Services

```bash
# View running containers
docker-compose ps

# Check API health
curl http://localhost:8000/health

# View logs
docker-compose logs -f fastapi
```

### Check WSL Resources

```bash
# Check memory
free -h

# Check disk space
df -h

# Check CPU
nproc
```

---

## Running the Project

### Start Services

```bash
cd ~/AI-FOS
docker-compose up -d
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f postgres
docker-compose logs -f kafka
```

### Restart Services

```bash
docker-compose restart
docker-compose restart fastapi
```

### Clean Rebuild

```bash
# Remove volumes and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## Accessing Services

### From Windows

All services are accessible on `localhost`:

| Service | URL | Port |
|---------|-----|------|
| FastAPI | http://localhost:8000 | 8000 |
| FastAPI Docs | http://localhost:8000/docs | 8000 |
| Grafana | http://localhost:3000 | 3000 |
| Jaeger | http://localhost:16686 | 16686 |
| Prometheus | http://localhost:9090 | 9090 |
| Kibana | http://localhost:5601 | 5601 |
| PostgreSQL | localhost:5432 | 5432 |
| Redis | localhost:6379 | 6379 |
| Kafka | localhost:9092 | 9092 |

### Credentials

| Service | Username | Password |
|---------|----------|----------|
| PostgreSQL | postgres | postgres |
| Grafana | admin | admin |
| Kibana | elastic | elastic |

### Database Connection

From Windows (using psql or tools):
```bash
psql -h localhost -U postgres -d voice_agent
```

---

## Troubleshooting

### Docker Service Not Running

**Problem:** `Cannot connect to Docker daemon`

**Solutions:**

1. Check if Docker is running:
```bash
sudo service docker status
# or
sudo systemctl status docker
```

2. Start Docker service:
```bash
sudo service docker start
# or
sudo systemctl start docker
```

3. Enable auto-start:
```bash
sudo systemctl enable docker
```

### Port Already in Use

**Problem:** `Bind for 0.0.0.0:8000 failed: port is already in use`

**Solution:** Find and stop the service using that port:
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill process (if needed)
sudo kill -9 <PID>

# Or use different port in compose
```

### Insufficient Disk Space

**Problem:** `No space left on device`

**Solutions:**
```bash
# Check disk usage
df -h

# Clean Docker resources
docker system prune -a --volumes

# Remove all containers and images
docker-compose down -v
docker system prune -af
```

### Memory Issues

**Problem:** Containers crashing or system slow

**Solutions:**
1. Increase WSL memory in `.wslconfig`:
   ```ini
   memory=8GB
   ```

2. Restart WSL:
   ```powershell
   wsl --shutdown
   ```

3. Reduce service count (run only needed services)

### Services Won't Start

**Problem:** `Error response from daemon`

**Solutions:**
```bash
# Check Docker logs
journalctl -u docker -n 50

# Try rebuilding
docker-compose down -v
docker-compose build --no-cache

# Start with limited services
docker-compose up -d postgres redis
```

### WSL Integration with Docker Desktop

If using Docker Desktop for Windows with WSL2 integration:

1. Open Docker Desktop settings
2. Go to "Resources" → "WSL Integration"
3. Enable integration for your Ubuntu distribution
4. Apply & restart Docker

---

## Performance Optimization

### Reduce Model Size

In `.env`:
```bash
STT_MODEL=tiny          # Instead of base/small/medium
TRANSLATION_MODEL=facebook/nllb-200-distilled-600M
```

### Limit Concurrent Calls

In `.env`:
```bash
MAX_CONCURRENT_CALLS=10
```

### Monitor Resources

```bash
# Real-time container stats
docker stats

# Check memory
free -m

# Check CPU
top
```

### Store Data in WSL

For better performance, keep project and Docker volumes in WSL home:
```bash
# Good (faster)
~/AI-FOS/

# Slower (Windows file system)
/mnt/c/Users/.../AI-FOS
```

---

## Update & Upgrade

### Update System Packages

```bash
sudo apt update
sudo apt upgrade
```

### Update Docker Images

```bash
docker-compose pull
docker-compose up -d
```

### Update Project Code

```bash
git pull origin main
docker-compose build --no-cache
docker-compose restart
```

---

## Advanced: Linux-Only Installation

If you want Docker only in WSL (not Docker Desktop):

```bash
# Install Docker only in WSL
sudo apt install -y docker.io docker-compose

# Start Docker
sudo service docker start

# Enable auto-start
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker ps
```

---

## Quick Reference

```bash
# Navigate to project
cd ~/AI-FOS

# Build
docker-compose build

# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Status
docker-compose ps

# Shell into container
docker-compose exec fastapi bash

# Clean rebuild
docker-compose down -v && docker-compose build
```

---

## Next Steps

1. ✅ Wait for all services to start (2-3 minutes)
2. ✅ Visit http://localhost:8000/health
3. ✅ Access Grafana: http://localhost:3000
4. ✅ Check logs: `docker-compose logs -f`
5. ✅ Make your first call using SIP

---

## Support

For issues:
1. Check `docker-compose logs -f` for error messages
2. Review troubleshooting section above
3. Ensure WSL2 is fully updated
4. Try clean rebuild: `docker-compose down -v && docker-compose build --no-cache`

---

**Last Updated**: March 14, 2026  
**WSL Support**: Windows 10/11 with WSL2  
**Status**: ✅ Production Ready
