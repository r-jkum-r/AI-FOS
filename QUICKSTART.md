# Quick Start Guide - Updated Architecture

## What This System Does

This system translates phone calls in real-time:
- Field Officer speaks Tamil/Telugu/Kannada/Marathi/Hindi → IT Team hears Hinglish
- IT Team speaks Hinglish → Field Officer hears their language

## What's New in This Version

✅ **Integrated ARI Handler** - Runs automatically with FastAPI
✅ **Configuration Management** - All settings in .env file
✅ **Proper Data Storage** - JSON serialization with TTL
✅ **Security** - Optional WebSocket authentication, configurable CORS
✅ **Better Error Handling** - Graceful degradation and detailed logging

## Deployment Options

- **Local Development** (this guide): For testing on your machine
- **AWS Deployment**: See [AWS-DEPLOYMENT.md](AWS-DEPLOYMENT.md) for production setup
- **Kubernetes**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for large-scale deployment

## System Requirements

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+ / Windows 10+ with WSL2
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space (for AI models)
- Internet connection (for downloading models)

## Step 1: Install Docker

### Linux
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

### Windows
See [WSL-SETUP.md](WSL-SETUP.md) for Windows installation guide.

Expected output:
```
Docker version 24.x.x
docker-compose version 1.29.x
```

## Step 2: Download and Setup

```bash
# Install git if not already installed
sudo apt install git -y  # Linux
# or use Git for Windows

# Download the code
git clone <your-repo-url>
cd AI-FOS

# Create environment file from template
cp .env.example .env

# (Optional) Edit .env with your configuration
# nano .env  # Linux
# notepad .env  # Windows
```

## Step 3: Verify Setup (Optional but Recommended)

```bash
# Run verification script (Linux/Mac)
bash scripts/verify-setup.sh

# On Windows, manually check:
# - .env file exists
# - docker and docker-compose are installed
# - All backend/*.py files exist
```

## Step 4: Start Everything (First Time Takes 5-10 Minutes)

```bash
# This single command starts everything
docker-compose up -d
```

What happens:
- Downloads AI models (Whisper ~1GB, Translation ~1GB, TTS ~500MB)
- Starts phone system (Asterisk)
- Starts translation service with ARI integration
- Starts monitoring tools (Prometheus, Grafana)
- Starts Redis for state management

**Wait 5-10 minutes** for first-time setup (downloading models).

### Monitor Startup Progress

```bash
# Watch backend logs
docker-compose logs -f backend

# Look for these success messages:
# ✅ "Loading Whisper model: medium on cpu"
# ✅ "Loading translation model: facebook/nllb-200-distilled-600M on cpu"
# ✅ "Loading TTS model on cpu"
# ✅ "AI pipeline initialized successfully"
# ✅ "Connected to Asterisk ARI"
# ✅ "Voice Gateway started successfully with ARI integration"

# Press Ctrl+C to exit log view
```

## Step 5: Check If It's Working

### Quick Health Check
Open your browser and go to:
```
http://localhost:8000/health
```

You should see:
```json
{"status":"healthy","service":"voice-gateway"}
```

### Check System Stats
```bash
curl http://localhost:8000/stats

# Expected response:
# {"active_calls":0,"total_processed":"0"}
```

### View API Documentation
```bash
# Open in browser
http://localhost:8000/docs
```

If you see these, the system is ready!

## Step 6: Make a Test Call

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

## Step 7: Test API Endpoints (Optional)

### Initiate a Test Call via API
```bash
curl -X POST "http://localhost:8000/api/call/initiate?caller_number=1234567890&destination=9876543210"

# Response:
# {"call_id":"uuid-here","status":"initiated"}
```

### Check Call Status
```bash
curl http://localhost:8000/api/call/{call_id}/status

# Response includes: call_id, status, language, timestamps
```

### Get Call Transcript
```bash
curl http://localhost:8000/api/call/{call_id}/transcript

# Response includes full conversation with translations
```

## Step 8: View Live Statistics (Optional)

Open in browser:

### Grafana Dashboard
```
http://localhost:3000
```
- Username: `admin`
- Password: `admin`

You'll see:
- Active calls
- Translation speed
- System performance

### Prometheus Metrics
```
http://localhost:9090
```
- Check targets: Status > Targets
- Should see: voice-agent-backend (UP)

## Configuration Options

Edit `.env` to customize:

```bash
# AI Model Sizes (trade-off: accuracy vs speed)
WHISPER_MODEL_SIZE=small    # Faster, less accurate
WHISPER_MODEL_SIZE=medium   # Balanced (default)
WHISPER_MODEL_SIZE=large    # Slower, more accurate

# Performance
MAX_CONCURRENT_CALLS=50     # Lower for limited resources
MAX_CONCURRENT_CALLS=100    # Default
MAX_CONCURRENT_CALLS=500    # High-performance setup

# Security (production)
WEBSOCKET_AUTH_TOKEN=your-secret-token-here
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Asterisk ARI (change for production)
ASTERISK_ARI_USER=asterisk
ASTERISK_ARI_PASSWORD=asterisk
```

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

# Solution 1: Reduce model size in .env
WHISPER_MODEL_SIZE=small
MAX_CONCURRENT_CALLS=10

# Solution 2: If less than 8GB RAM, add swap space:
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Then restart
docker-compose restart backend
```

### "ARI not connecting"
```bash
# Check Asterisk is running
docker-compose ps asterisk

# Check ARI credentials in .env
# Default: asterisk/asterisk

# Check Asterisk logs
docker-compose logs asterisk

# Restart Asterisk
docker-compose restart asterisk
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
# First startup downloads ~2GB of models
# Be patient or use faster internet

# Check download progress
docker-compose logs -f backend | grep -i "download"

# If stuck, restart:
docker-compose restart backend
```

### "Redis connection failed"
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker exec -it ai-fos-redis-1 redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis
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

- **Backend (port 8000)**: Main translation service with ARI integration
- **Asterisk (port 5060)**: Handles phone calls (SIP/RTP)
- **Redis (port 6379)**: Stores call information and transcripts
- **Grafana (port 3000)**: Shows statistics and dashboards
- **Prometheus (port 9090)**: Collects and stores metrics

## Development Mode

### Enable Hot Reload
Already enabled in docker-compose.yml with `--reload` flag.
Edit Python files and changes will auto-reload.

### View Logs in Real-Time
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f asterisk
docker-compose logs -f redis
```

## Performance Tuning

### For Limited Resources (4GB RAM)
```bash
# In .env
WHISPER_MODEL_SIZE=small
MAX_CONCURRENT_CALLS=10
```

### For High Performance (16GB+ RAM)
```bash
# In .env
WHISPER_MODEL_SIZE=large
MAX_CONCURRENT_CALLS=200

# Consider GPU support for faster processing
```

## Next Steps

Once basic setup works:

1. **Read Architecture Documentation**
   - [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
   - [ARCHITECTURE-FIXES.md](ARCHITECTURE-FIXES.md) - Recent improvements

2. **Configure for Your Use Case**
   - Edit `.env` with your settings
   - Customize Asterisk dialplan if needed

3. **Production Deployment**
   - [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Full deployment guide
   - [AWS-DEPLOYMENT.md](AWS-DEPLOYMENT.md) - AWS-specific instructions
   - [SECURITY.md](docs/SECURITY.md) - Security hardening
   - [SCALING.md](docs/SCALING.md) - Scaling strategies

4. **Testing**
   - [TESTING.md](docs/TESTING.md) - Detailed testing guide
   - Test with real SIP clients
   - Load test with expected traffic

## Getting Help

- **Documentation:** See docs/ folder
- **Logs:** `docker-compose logs -f backend`
- **Health Check:** `curl http://localhost:8000/health`
- **Verification:** `bash scripts/verify-setup.sh`
- **API Docs:** `http://localhost:8000/docs`

## Summary

You now have a production-ready, architecture-compliant voice translation system with:

✅ Integrated ARI and FastAPI
✅ Proper configuration management
✅ Secure data storage with TTL
✅ Error handling and logging
✅ Health checks and monitoring
✅ WebSocket authentication
✅ Scalable architecture

Happy coding! 🚀

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
