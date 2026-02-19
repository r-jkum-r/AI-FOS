# Corporate WSL Ubuntu Setup Guide

This guide is specifically for running the AI Voice Agent on WSL Ubuntu within a corporate laptop environment.

## Corporate Environment Considerations

### Common Corporate Restrictions
- 🔒 Proxy servers for internet access
- 🔒 SSL/TLS inspection (corporate certificates)
- 🔒 Firewall restrictions on ports
- 🔒 VPN requirements
- 🔒 Limited admin/sudo access
- 🔒 Antivirus software interference
- 🔒 Docker Desktop restrictions

## Prerequisites Check

### 1. Check WSL Version
```bash
wsl --version
# Should show WSL version 2
```

### 2. Check Ubuntu Version
```bash
lsb_release -a
# Should be Ubuntu 20.04 or newer
```

### 3. Check Available Resources
```bash
# Check memory
free -h
# Need at least 8GB available

# Check disk space
df -h
# Need at least 20GB free
```

## Step 1: Configure Corporate Proxy (If Required)

### Check if Proxy is Required
```bash
# Try to access internet
curl -I https://google.com

# If it fails, you likely need proxy configuration
```

### Configure Proxy for WSL
```bash
# Edit .bashrc
nano ~/.bashrc

# Add these lines at the end (replace with your corporate proxy):
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1,.company.com"

# Save and reload
source ~/.bashrc
```

### Configure Proxy for Docker
```bash
# Create Docker config directory
mkdir -p ~/.docker

# Create config file
nano ~/.docker/config.json

# Add this content (replace with your proxy):
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.company.com:8080",
      "httpsProxy": "http://proxy.company.com:8080",
      "noProxy": "localhost,127.0.0.1"
    }
  }
}
```

### Configure Proxy for APT
```bash
# Create apt proxy config
sudo nano /etc/apt/apt.conf.d/proxy.conf

# Add these lines:
Acquire::http::Proxy "http://proxy.company.com:8080";
Acquire::https::Proxy "http://proxy.company.com:8080";
```

## Step 2: Handle Corporate SSL Certificates

### Check for SSL Issues
```bash
# Test SSL connection
curl https://pypi.org

# If you see SSL certificate errors, continue below
```

### Install Corporate Root Certificate
```bash
# Get the certificate from your IT department
# Usually named something like: company-root-ca.crt

# Copy it to WSL (from Windows)
cp /mnt/c/Users/YourUsername/Downloads/company-root-ca.crt ~/

# Install the certificate
sudo cp ~/company-root-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Verify
curl https://pypi.org
```

### Configure Python/pip for Corporate SSL
```bash
# Create pip config
mkdir -p ~/.pip
nano ~/.pip/pip.conf

# Add this content:
[global]
cert = /etc/ssl/certs/ca-certificates.crt
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
```

## Step 3: Install Docker in WSL

### Option A: Docker Desktop (If Allowed)
```bash
# If your company allows Docker Desktop:
# 1. Install Docker Desktop for Windows
# 2. Enable WSL 2 integration in Docker Desktop settings
# 3. Select your Ubuntu distribution

# Verify in WSL:
docker --version
docker-compose --version
```

### Option B: Docker in WSL (Without Docker Desktop)
```bash
# Update packages
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo service docker start

# Enable Docker to start automatically
echo "sudo service docker start" >> ~/.bashrc

# Verify
docker --version
```

### Configure Docker for Corporate Environment
```bash
# Create Docker daemon config
sudo mkdir -p /etc/docker
sudo nano /etc/docker/daemon.json

# Add this content (adjust for your environment):
{
  "dns": ["8.8.8.8", "8.8.4.4"],
  "insecure-registries": [],
  "registry-mirrors": []
}

# Restart Docker
sudo service docker restart
```

## Step 4: Clone and Setup Project

```bash
# Navigate to your workspace
cd ~

# Clone the repository
git clone <your-repo-url>
cd AI-FOS

# If git fails due to SSL, temporarily disable SSL verification:
# git config --global http.sslVerify false
# (Re-enable after cloning: git config --global http.sslVerify true)

# Create environment file
cp .env.example .env

# Edit configuration
nano .env
```

## Step 5: Configure for Corporate Network

### Update .env for Corporate Environment
```bash
# Edit .env
nano .env

# Important settings for corporate environment:

# Use internal DNS if needed
# REDIS_URL=redis://redis:6379

# If you have internal Docker registry:
# Add registry prefix to images in docker-compose.yml

# Adjust CORS for corporate domains:
CORS_ORIGINS=http://localhost:8000,http://localhost:3000

# Set smaller model sizes if resources are limited:
WHISPER_MODEL_SIZE=small
MAX_CONCURRENT_CALLS=10
```

### Update docker-compose.yml for Corporate Network
```bash
nano docker-compose.yml

# Add DNS servers if needed:
# Under each service, add:
#   dns:
#     - 8.8.8.8
#     - 8.8.4.4

# Or use your corporate DNS:
#   dns:
#     - 10.x.x.x  # Your corporate DNS
```

## Step 6: Handle Firewall and Port Issues

### Check Available Ports
```bash
# Check if ports are available
sudo netstat -tulpn | grep -E ':(5060|8000|6379|3000|9090)'

# If ports are in use, change them in docker-compose.yml
```

### Configure Windows Firewall (If Needed)
```powershell
# Run in Windows PowerShell as Administrator:

# Allow WSL ports
New-NetFirewallRule -DisplayName "WSL Voice Agent" -Direction Inbound -LocalPort 8000,5060,3000,9090 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "WSL Voice Agent UDP" -Direction Inbound -LocalPort 5060,10000-10100 -Protocol UDP -Action Allow
```

## Step 7: Start Services

### First-Time Setup
```bash
# Start Docker if not running
sudo service docker start

# Pull images (may take time on corporate network)
docker-compose pull

# Start services
docker-compose up -d

# Monitor progress (Ctrl+C to exit)
docker-compose logs -f backend
```

### Expected First-Time Issues and Solutions

#### Issue: Slow Download Speeds
```bash
# Corporate networks can be slow
# Be patient, first download takes 10-20 minutes

# Check progress
docker-compose logs backend | grep -i download
```

#### Issue: SSL Certificate Errors
```bash
# If you see SSL errors in logs:
docker-compose down

# Add to docker-compose.yml under backend service:
#   environment:
#     - REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
#     - CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

docker-compose up -d
```

#### Issue: Connection Timeouts
```bash
# Increase timeout in docker-compose.yml:
# Add under backend service:
#   environment:
#     - PIP_DEFAULT_TIMEOUT=300
```

## Step 8: Verify Installation

### Check Services
```bash
# Check all containers are running
docker-compose ps

# Should see:
# - redis (Up)
# - backend (Up)
# - asterisk (Up)
# - prometheus (Up)
# - grafana (Up)
```

### Check Health
```bash
# From WSL
curl http://localhost:8000/health

# From Windows browser
# http://localhost:8000/health
```

### Run Verification Script
```bash
bash scripts/verify-setup.sh
```

## Step 9: Access from Windows

### Access Web Interfaces from Windows Browser

```
Backend API:     http://localhost:8000/docs
Grafana:         http://localhost:3000
Prometheus:      http://localhost:9090
Health Check:    http://localhost:8000/health
```

### Access from Other Machines on Corporate Network

```bash
# Get your Windows IP address
# In Windows PowerShell:
ipconfig

# Look for "IPv4 Address" under your network adapter
# Example: 192.168.1.100

# Access from other machines:
# http://192.168.1.100:8000/docs
```

## Corporate-Specific Troubleshooting

### Issue: "Cannot connect to Docker daemon"
```bash
# Start Docker service
sudo service docker start

# Check status
sudo service docker status

# If it fails, check logs
sudo journalctl -u docker
```

### Issue: "Permission denied" errors
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login to WSL
exit
# Then reopen WSL terminal

# Or use newgrp
newgrp docker
```

### Issue: Antivirus Blocking Docker
```bash
# Contact IT to whitelist:
# - Docker Desktop
# - WSL processes
# - Ports: 8000, 5060, 3000, 9090, 6379
```

### Issue: VPN Disconnects Breaking Services
```bash
# Add to ~/.bashrc to auto-restart Docker:
if ! sudo service docker status > /dev/null 2>&1; then
    sudo service docker start
fi

# Restart services after VPN reconnect:
docker-compose restart
```

### Issue: Out of Memory
```bash
# Check WSL memory limit
# In Windows, create/edit: C:\Users\YourUsername\.wslconfig

[wsl2]
memory=8GB
processors=4
swap=8GB

# Restart WSL from PowerShell:
wsl --shutdown
# Then reopen WSL
```

### Issue: Disk Space Issues
```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a

# Clean WSL
sudo apt clean
sudo apt autoremove
```

## Performance Optimization for Corporate Laptops

### Reduce Resource Usage
```bash
# Edit .env
nano .env

# Use smaller models:
WHISPER_MODEL_SIZE=small
MAX_CONCURRENT_CALLS=5

# Restart services
docker-compose restart backend
```

### Limit Docker Resources
```bash
# Edit docker-compose.yml
# Add under backend service:
#   deploy:
#     resources:
#       limits:
#         cpus: '2'
#         memory: 4G
```

## Working Offline (After Initial Setup)

### Cache Models for Offline Use
```bash
# After first successful run, models are cached in Docker volume
# You can work offline after that

# To backup models:
docker run --rm -v ai-fos_ai-models:/data -v $(pwd):/backup ubuntu tar czf /backup/ai-models-backup.tar.gz /data
```

## Security Considerations for Corporate Environment

### 1. Don't Expose Ports Externally
```bash
# In docker-compose.yml, bind to localhost only:
# Change:
#   ports:
#     - "8000:8000"
# To:
#   ports:
#     - "127.0.0.1:8000:8000"
```

### 2. Use Strong Credentials
```bash
# Edit .env
ASTERISK_ARI_PASSWORD=<strong-password>
WEBSOCKET_AUTH_TOKEN=<random-token>

# Generate random token:
openssl rand -hex 32
```

### 3. Enable Authentication
```bash
# In .env
WEBSOCKET_AUTH_TOKEN=your-generated-token-here
```

### 4. Regular Updates
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

## Daily Usage Workflow

### Starting Work
```bash
# Open WSL Ubuntu
# Start Docker
sudo service docker start

# Start services
cd ~/AI-FOS
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### During Work
```bash
# View logs
docker-compose logs -f backend

# Check stats
curl http://localhost:8000/stats

# Access Grafana
# Open browser: http://localhost:3000
```

### Ending Work
```bash
# Stop services (optional - saves resources)
docker-compose down

# Or leave running for faster restart
```

## Getting Help

### Check Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs asterisk

# Follow logs
docker-compose logs -f
```

### Run Diagnostics
```bash
# System info
uname -a
docker --version
docker-compose --version

# Resource usage
free -h
df -h
docker stats

# Network
ip addr
netstat -tulpn
```

### Contact IT Support
If you encounter corporate-specific issues:
- Proxy configuration
- SSL certificate installation
- Firewall rules
- VPN compatibility
- Antivirus exceptions
- Resource allocation

## Summary

You're now set up to run the AI Voice Agent on WSL Ubuntu in a corporate environment with:

✅ Proxy configuration
✅ Corporate SSL certificates
✅ Docker in WSL
✅ Firewall configuration
✅ Resource optimization
✅ Security best practices
✅ Offline capability
✅ Daily workflow

For general usage, see [QUICKSTART.md](QUICKSTART.md)
For troubleshooting, see [FIX-SSL-ISSUES.md](FIX-SSL-ISSUES.md)
