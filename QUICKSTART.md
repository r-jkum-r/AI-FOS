# Quick Start Guide - Linux

## What This System Does

This system translates phone calls in real-time:
- Field Officer speaks Tamil/Telugu/Hindi → IT Team hears Hinglish
- IT Team speaks Hinglish → Field Officer hears their language

## System Requirements

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
- 8GB RAM minimum (16GB recommended)
- 50GB free disk space
- Internet connection (for downloading models)

## Step 1: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (so you don't need sudo)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Logout and login again for group changes to take effect
# Or run: newgrp docker

# Verify installation
docker --version
docker-compose --version
```

Expected output:
```
Docker version 24.x.x
docker-compose version 1.29.x
```

## Step 2: Download This Project

```bash
# Install git if not already installed
sudo apt install git -y

# Download the code
git clone <your-repo-url>
cd voice-ai-agent

# Check files are there
ls -la
```

You should see folders: `backend/`, `asterisk/`, `infra/`, `docs/`

## Step 3: Start Everything (First Time Takes 5-10 Minutes)

```bash
# This single command starts everything
docker-compose up -d
```

What happens:
- Downloads AI models (Whisper, Translation, Voice synthesis)
- Starts phone system (Asterisk)
- Starts translation service
- Starts monitoring tools

**Wait 5-10 minutes** for first-time setup (downloading models).

## Step 4: Check If It's Working

Open your browser and go to:
```
http://localhost:8000/health
```

You should see:
```json
{"status":"healthy","service":"voice-gateway"}
```

If you see this, the system is ready!

## Step 5: Make a Test Call

### Option A: Using Linphone on Linux Desktop

```bash
# Install Linphone
sudo apt install linphone -y

# Run Linphone
linphone &
```

**Setup in Linphone:**
1. Click "Use SIP Account"
2. Enter these details:
   - Username: `test-user`
   - Password: (leave blank)
   - Domain: `localhost:5060`
   - Transport: UDP
3. Click "Sign In"

**Make a test call:**
1. In Linphone, dial: `1000`
2. Press call button
3. Speak in Tamil/Telugu/Hindi
4. You'll hear Hinglish translation!

### Option B: Using Mobile Phone (Android/iPhone)

1. **Download Linphone app** from Play Store or App Store

2. **Find your Linux server IP:**
   ```bash
   # Get your IP address
   hostname -I | awk '{print $1}'
   ```
   Example output: `192.168.1.100`

3. **Setup in Linphone app:**
   - Username: `test-user`
   - Password: (leave blank)
   - Domain: `YOUR_SERVER_IP:5060` (use IP from step 2)
   - Transport: UDP

4. **Make sure phone and server are on same network**

5. **Dial `1000` and test**

### Option C: Test Without Phone (Quick Check)

```bash
# Check if services are running
docker-compose ps

# You should see:
# - redis (running)
# - asterisk (running)
# - backend (running)
# - prometheus (running)
# - grafana (running)
```

## Step 6: View Live Statistics (Optional)

Open in browser:
```
http://localhost:3000
```
- Username: `admin`
- Password: `admin`

You'll see:
- Active calls
- Translation speed
- System performance

## Common Issues & Solutions

### "Permission denied" when running docker
```bash
# Add yourself to docker group
sudo usermod -aG docker $USER

# Logout and login, or run:
newgrp docker
```

### "Port already in use"
```bash
# Check what's using the port
sudo netstat -tulpn | grep 5060
sudo netstat -tulpn | grep 8000

# Stop the system
docker-compose down

# Start again
docker-compose up -d
```

### "Backend not starting" or "Out of memory"
```bash
# Check what's wrong
docker-compose logs backend

# Check available memory
free -h

# If less than 8GB RAM, you need to:
# 1. Close other applications
# 2. Add swap space:
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### "Can't connect from phone"
```bash
# Check if firewall is blocking
sudo ufw status

# Allow SIP and RTP ports
sudo ufw allow 5060/udp
sudo ufw allow 5060/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 10000:10100/udp

# Check if services are listening
sudo netstat -tulpn | grep 5060
```

### "Models downloading too slow"
```bash
# Check download progress
docker-compose logs -f backend | grep -i download

# If stuck, restart:
docker-compose restart backend
```

### "Asterisk not starting"
```bash
# Check Asterisk logs
docker-compose logs asterisk

# Restart Asterisk
docker-compose restart asterisk

# Check if it's running
docker-compose exec asterisk asterisk -rx "core show version"
```

## Stop the System

```bash
# Stop everything
docker-compose down

# Stop and delete all data
docker-compose down -v
```

## What Each Service Does

- **Backend (port 8000)**: Main translation service
- **Asterisk (port 5060)**: Handles phone calls
- **Redis (port 6379)**: Stores call information
- **Grafana (port 3000)**: Shows statistics
- **Prometheus (port 9090)**: Collects metrics

## Next Steps

Once basic setup works:
1. Read [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production setup
2. Read [TESTING.md](docs/TESTING.md) for detailed testing
3. Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) to understand how it works

## Useful Commands

### Check logs
```bash
# See all logs
docker-compose logs

# See only backend logs
docker-compose logs backend

# See only Asterisk logs
docker-compose logs asterisk

# Follow logs in real-time (Ctrl+C to exit)
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Check system resources
```bash
# Check Docker containers
docker-compose ps

# Check CPU and memory usage
docker stats

# Check disk space
df -h

# Check memory
free -h
```

### Restart services
```bash
# Restart everything
docker-compose restart

# Restart only backend
docker-compose restart backend

# Restart only Asterisk
docker-compose restart asterisk
```

### Clean up
```bash
# Stop everything
docker-compose down

# Stop and remove all data
docker-compose down -v

# Remove downloaded models (to free space)
docker volume prune

# Remove all unused Docker images
docker system prune -a
```

## Performance Tips

### For better performance:
```bash
# Check if you have GPU
lspci | grep -i nvidia

# If you have NVIDIA GPU, install CUDA support:
# Follow: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/

# Then rebuild with GPU support:
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Monitor system in real-time:
```bash
# Install htop
sudo apt install htop -y

# Run htop
htop

# Look for:
# - CPU usage (should be < 80%)
# - Memory usage (should have 2GB+ free)
# - Load average (should be < number of CPU cores)
```

## Production Deployment

For production use (handling 100+ concurrent calls):

1. **Use Kubernetes** instead of Docker Compose:
   ```bash
   # See full guide
   cat docs/DEPLOYMENT.md
   ```

2. **Use dedicated server** with:
   - 16GB+ RAM
   - 8+ CPU cores
   - SSD storage
   - Static public IP

3. **Enable monitoring**:
   - Grafana: http://your-server:3000
   - Prometheus: http://your-server:9090

## Need Help?

1. Check logs first: `docker-compose logs -f`
2. Read error messages carefully
3. Check [DEPLOYMENT.md](docs/DEPLOYMENT.md) for advanced setup
4. Check [TESTING.md](docs/TESTING.md) for testing guide
5. Check [ARCHITECTURE.md](docs/ARCHITECTURE.md) to understand the system
