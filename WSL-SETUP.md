# WSL Ubuntu Setup Guide

## What This System Does

This system translates phone calls in real-time:
- Field Officer speaks Tamil/Telugu/Hindi → IT Team hears Hinglish
- IT Team speaks Hinglish → Field Officer hears their language

## Prerequisites

- Windows 10/11 with WSL2 installed
- Ubuntu on WSL (20.04 or 22.04)
- 16GB RAM on Windows (8GB minimum)
- 50GB free disk space

## Step 1: Verify WSL2 Setup

### 1.1 Check WSL Version

Open PowerShell or Windows Terminal and run:

```powershell
wsl --list --verbose
```

You should see:
```
  NAME            STATE           VERSION
* Ubuntu          Running         2
```

If VERSION shows "1", upgrade to WSL2:

```powershell
wsl --set-version Ubuntu 2
```

### 1.2 Configure WSL2 Resources

Create or edit `C:\Users\YOUR_USERNAME\.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
swap=4GB
```

Restart WSL:
```powershell
wsl --shutdown
wsl
```

## Step 2: Install Docker in WSL

Open WSL Ubuntu terminal:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Install git
sudo apt install git -y

# Start Docker service
    sudo service docker start

# Enable Docker to start automatically
echo "sudo service docker start" >> ~/.bashrc
```

**Important:** Close and reopen WSL terminal for group changes to take effect.

### 2.1 Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check Docker is running
docker ps

# Check Docker Compose
docker-compose --version
```

Expected output:
```
Docker version 24.x.x
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
docker-compose version 1.29.x
```

## Step 3: Download the Project

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone <your-repo-url>
cd voice-ai-agent

# Verify files
ls -la
```

You should see: `backend/`, `asterisk/`, `infra/`, `docs/`, `docker-compose.yml`

## Step 4: Get Your Windows IP Address

The system needs your Windows IP for phone connections.

### Option A: From WSL
```bash
# Get Windows host IP
ip route show | grep -i default | awk '{ print $3}'
```

### Option B: From Windows PowerShell
```powershell
ipconfig
```

Look for "Wireless LAN adapter Wi-Fi" or "Ethernet adapter" → IPv4 Address

Example: `192.168.1.100`

**Save this IP - you'll need it later!**

## Step 5: Configure Asterisk

Update the SIP configuration with your Windows IP:

```bash
# Replace YOUR_PUBLIC_IP with your Windows IP from Step 4
export WINDOWS_IP="172.22.64.1"  # Change this!

# Update Asterisk config
sed -i "s/YOUR_PUBLIC_IP/$WINDOWS_IP/g" asterisk/sip.conf

# Verify the change
grep "external_media_address" asterisk/sip.conf
```

Should show your Windows IP.

## Step 6: Start the System

```bash
# Make sure Docker is running
sudo service docker start

# Start all services (first time takes 10-15 minutes)
docker-compose up -d

# Watch the startup logs
docker-compose logs -f backend
```

**Wait for this message:**
```
INFO: Application startup complete.
```

Press `Ctrl+C` to exit logs (services keep running).

### What's Happening?
- Downloading AI models (Whisper, NLLB, Coqui TTS) - ~5GB
- Starting Asterisk phone system
- Starting translation service
- Starting Redis database
- Starting monitoring tools

## Step 7: Verify Everything is Running

```bash
# Check all containers are up
docker-compose ps
```

All services should show "Up":
```
NAME                STATUS
redis               Up
asterisk            Up
backend             Up
prometheus          Up
grafana             Up
```

### Test the API

```bash
# From WSL
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"voice-gateway"}
```

### Test from Windows Browser

Open in Windows browser:
```
http://localhost:8000/health
```

Should show the same JSON response.

## Step 8: Test with Phone

### Option A: Test from Windows (Easiest)

1. **Download Linphone for Windows:**
   - Go to: https://www.linphone.org/
   - Download Windows version
   - Install and open

2. **Configure SIP Account:**
   - Click "Use SIP Account"
   - Username: `test-user`
   - Password: (leave blank)
   - Domain: `localhost:5060`
   - Transport: UDP
   - Click "Sign In"

3. **Make Test Call:**
   - Dial: `1000`
   - Click call
   - Speak in Tamil/Telugu/Hindi
   - Listen for Hinglish translation!

### Option B: Test from Mobile Phone

1. **Download Linphone app** (Play Store or App Store)

2. **Get your Windows IP** (from Step 4)

3. **Configure in Linphone app:**
   - Username: `test-user`
   - Password: (leave blank)
   - Domain: `YOUR_WINDOWS_IP:5060` (e.g., `192.168.1.100:5060`)
   - Transport: UDP

4. **Make sure phone and PC are on same WiFi**

5. **Dial `1000` and test**

## Step 9: Access Monitoring Dashboards

### Grafana (Statistics)

**From Windows browser:**
```
http://localhost:3000
```

**Login:**
- Username: `admin`
- Password: `admin`

You'll see:
- Active calls
- Translation speed
- System performance

### Prometheus (Metrics)

**From Windows browser:**
```
http://localhost:9090
```

## WSL-Specific Tips

### Start Docker Automatically

Add to `~/.bashrc`:

```bash
# Start Docker on WSL startup
if ! service docker status > /dev/null 2>&1; then
    sudo service docker start > /dev/null 2>&1
fi
```

Then:
```bash
source ~/.bashrc
```

### Access WSL Files from Windows

In Windows File Explorer, go to:
```
\\wsl$\Ubuntu\home\YOUR_USERNAME\voice-ai-agent
```

### Access Windows Files from WSL

```bash
cd /mnt/c/Users/YOUR_USERNAME/
```

### Port Forwarding (If Needed)

WSL2 usually auto-forwards ports, but if you have issues:

**From Windows PowerShell (as Administrator):**
```powershell
# Forward port 5060 (SIP)
netsh interface portproxy add v4tov4 listenport=5060 listenaddress=0.0.0.0 connectport=5060 connectaddress=localhost

# Forward port 8000 (API)
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=localhost

# View all port forwards
netsh interface portproxy show all
```

## Common WSL Issues & Solutions

### "Docker daemon not running"

```bash
# Start Docker
sudo service docker start

# Check status
sudo service docker status

# If it fails, try:
sudo dockerd
```

### "Cannot connect to Docker daemon"

```bash
# Check if Docker is running
ps aux | grep docker

# Restart Docker
sudo service docker restart

# Add yourself to docker group again
sudo usermod -aG docker $USER

# Logout and login
exit
# Then reopen WSL
```

### "Port already in use"

```bash
# Check what's using the port
sudo netstat -tulpn | grep 5060
sudo netstat -tulpn | grep 8000

# Stop the services
docker-compose down

# Start again
docker-compose up -d
```

### "Out of memory"

```bash
# Check memory usage
free -h

# Increase WSL memory in .wslconfig (see Step 1.2)
# Then restart WSL from PowerShell:
# wsl --shutdown
```

### "Can't connect from phone"

```bash
# Check Windows Firewall
# Open Windows Defender Firewall
# Allow ports: 5060, 8000, 10000-10100

# Or temporarily disable firewall for testing
```

### "Models downloading too slow"

```bash
# Check download progress
docker-compose logs -f backend | grep -i download

# If stuck, restart:
docker-compose restart backend
```

## Useful Commands

### Managing Services

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# Restart everything
docker-compose restart

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f asterisk

# Check status
docker-compose ps

# Check resource usage
docker stats
```

### System Monitoring

```bash
# Check WSL memory usage
free -h

# Check disk space
df -h

# Check CPU usage
top
# Or install htop:
sudo apt install htop -y
htop
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove all data (including models)
docker-compose down -v

# Clean up Docker
docker system prune -a

# Free up WSL disk space
# From PowerShell:
# wsl --shutdown
# Optimize-VHD -Path C:\Users\YOUR_USERNAME\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_*\LocalState\ext4.vhdx -Mode Full
```

## Performance Optimization

### 1. Allocate More Resources

Edit `C:\Users\YOUR_USERNAME\.wslconfig`:

```ini
[wsl2]
memory=12GB
processors=6
swap=8GB
localhostForwarding=true
```

### 2. Use WSL2 Native Docker

Instead of Docker Desktop, use Docker directly in WSL (already done in Step 2).

### 3. Store Project in WSL Filesystem

Keep the project in WSL (`/home/username/`) not Windows (`/mnt/c/`).
WSL filesystem is much faster!

## Stopping the System

### Temporary Stop (Keep Data)

```bash
docker-compose stop
```

### Complete Shutdown

```bash
docker-compose down
```

### Shutdown WSL

From Windows PowerShell:
```powershell
wsl --shutdown
```

## Next Steps

Once everything works on WSL:

1. **Test thoroughly** with multiple calls
2. **Monitor performance** via Grafana
3. **Deploy to AWS** for production: See [AWS-DEPLOYMENT.md](AWS-DEPLOYMENT.md)
4. **Read architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
5. **Setup testing**: [docs/TESTING.md](docs/TESTING.md)

## Troubleshooting Checklist

- [ ] WSL2 is installed and running
- [ ] Docker is installed in WSL (not Docker Desktop)
- [ ] Docker service is started (`sudo service docker start`)
- [ ] You're in docker group (`groups | grep docker`)
- [ ] Windows IP is configured in `asterisk/sip.conf`
- [ ] All containers are running (`docker-compose ps`)
- [ ] API responds (`curl http://localhost:8000/health`)
- [ ] Windows Firewall allows ports 5060, 8000
- [ ] Phone and PC are on same WiFi network

## Getting Help

```bash
# Check all logs
docker-compose logs

# Check specific service
docker-compose logs backend
docker-compose logs asterisk

# Check Docker status
sudo service docker status

# Check WSL version
wsl --list --verbose

# Check system resources
free -h
df -h
```

## Quick Reference

| Service | Port | Access From Windows |
|---------|------|---------------------|
| API | 8000 | http://localhost:8000 |
| SIP | 5060 | localhost:5060 |
| Grafana | 3000 | http://localhost:3000 |
| Prometheus | 9090 | http://localhost:9090 |
| Redis | 6379 | localhost:6379 |

## Support

- WSL Documentation: https://docs.microsoft.com/en-us/windows/wsl/
- Docker in WSL: https://docs.docker.com/desktop/wsl/
- Project Docs: [docs/](docs/)
- AWS Deployment: [AWS-DEPLOYMENT.md](AWS-DEPLOYMENT.md)
