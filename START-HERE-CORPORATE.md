# 🚀 START HERE - Corporate WSL Ubuntu Setup

**Welcome!** This guide is specifically for your setup: WSL Ubuntu on a corporate laptop.

## 📖 Your Reading Path

### 1️⃣ First Time Setup (Do Once)
Read: **[CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md)**

This covers:
- Corporate proxy configuration
- SSL certificate handling
- Docker installation in WSL
- Firewall and VPN considerations
- First-time project setup

**Time needed:** 30-60 minutes

### 2️⃣ Daily Usage (Bookmark This!)
Read: **[QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md)**

Quick commands for:
- Starting/stopping services
- Checking status
- Common troubleshooting
- Accessing web interfaces

**Time needed:** 2 minutes daily

### 3️⃣ Understanding the System (Optional)
Read: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**

Learn about:
- How the system works
- Component interactions
- Data flow
- AI pipeline

**Time needed:** 15 minutes

## ⚡ Super Quick Start (If Everything Works)

```bash
# Open WSL Ubuntu terminal
cd ~/AI-FOS

# Create config
cp .env.example .env

# Start everything
sudo service docker start
docker-compose up -d

# Wait 5-10 minutes for first-time setup
# Then check:
curl http://localhost:8000/health
```

**If this works:** You're done! Bookmark [QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md)

**If this fails:** Follow [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) step by step

## 🎯 What You'll Get

After setup, you'll have:

✅ **AI Voice Translation System** running locally
✅ **Web Dashboard** at http://localhost:3000
✅ **API Documentation** at http://localhost:8000/docs
✅ **Real-time Monitoring** with Prometheus & Grafana
✅ **Full Control** over configuration and resources

## 🔍 Common Corporate Issues (And Solutions)

### Issue: Proxy Blocking Downloads
**Solution:** Configure proxy in [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) Step 1

### Issue: SSL Certificate Errors
**Solution:** Install corporate certificates in [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) Step 2

### Issue: VPN Disconnects Breaking Services
**Solution:** Auto-restart script in [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) Troubleshooting

### Issue: Slow Performance
**Solution:** Resource optimization in [QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md) Performance Tuning

### Issue: Out of Memory
**Solution:** WSL memory configuration in [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) Troubleshooting

## 📊 System Requirements

### Minimum (Will Work)
- 8GB RAM
- 20GB free disk space
- WSL 2
- Ubuntu 20.04+

### Recommended (Better Performance)
- 16GB RAM
- 50GB free disk space
- WSL 2
- Ubuntu 22.04

### Check Your System
```bash
# In WSL Ubuntu:
free -h          # Check RAM
df -h            # Check disk space
lsb_release -a   # Check Ubuntu version
wsl --version    # In Windows PowerShell
```

## 🎓 Learning Path

### Day 1: Setup
1. Read [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md)
2. Complete installation
3. Verify with health check
4. Bookmark [QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md)

### Day 2: Explore
1. Open http://localhost:8000/docs
2. Try API endpoints
3. Check Grafana dashboard
4. Review logs: `docker-compose logs -f`

### Day 3: Understand
1. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
2. Review configuration in .env
3. Experiment with settings
4. Test with SIP client (optional)

### Ongoing: Maintain
1. Check [QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md) daily
2. Monitor resource usage
3. Update regularly
4. Backup configuration

## 🆘 When Things Go Wrong

### Step 1: Check Logs
```bash
docker-compose logs backend
```

### Step 2: Check Resources
```bash
free -h
df -h
docker stats
```

### Step 3: Restart Services
```bash
docker-compose restart
```

### Step 4: Full Reset
```bash
docker-compose down
docker-compose up -d
```

### Step 5: Consult Documentation
- [QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md) - Quick fixes
- [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) - Detailed troubleshooting
- [FIX-SSL-ISSUES.md](FIX-SSL-ISSUES.md) - SSL problems

## 💡 Pro Tips for Corporate Environment

1. **Keep Docker Running**
   - Don't stop Docker between sessions
   - Faster startup next time

2. **Use Smaller Models**
   - Set `WHISPER_MODEL_SIZE=small` in .env
   - Better for laptop resources

3. **Bookmark URLs**
   - http://localhost:8000/docs
   - http://localhost:3000
   - Save time accessing interfaces

4. **Monitor Resources**
   - Run `docker stats` occasionally
   - Catch issues early

5. **Backup Your .env**
   - Copy .env to .env.backup
   - Easy recovery if needed

6. **Work Offline**
   - After first setup, models are cached
   - Can work without internet

7. **Auto-Start Docker**
   - Add to ~/.bashrc (see corporate guide)
   - One less thing to remember

## 📞 Getting Help

### Self-Service (Fastest)
1. Check [QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md)
2. Search logs: `docker-compose logs | grep -i error`
3. Run verification: `bash scripts/verify-setup.sh`

### Documentation
1. [CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md) - Corporate-specific
2. [QUICKSTART.md](QUICKSTART.md) - General guide
3. [FIX-SSL-ISSUES.md](FIX-SSL-ISSUES.md) - SSL problems

### IT Support (If Needed)
Contact your IT department for:
- Proxy configuration details
- Corporate SSL certificates
- Firewall exceptions
- VPN compatibility
- Resource allocation

## ✅ Success Checklist

After setup, verify:

- [ ] Docker running: `sudo service docker status`
- [ ] Services up: `docker-compose ps` (all "Up")
- [ ] Health check: `curl http://localhost:8000/health` returns "healthy"
- [ ] API docs: http://localhost:8000/docs loads
- [ ] Grafana: http://localhost:3000 loads (admin/admin)
- [ ] No errors: `docker-compose logs --tail=50` looks clean
- [ ] Bookmarked: [QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md)

## 🎉 You're Ready!

Once all checks pass:
1. You have a working AI voice translation system
2. You can access it from Windows browser
3. You can monitor it with Grafana
4. You can test it with API calls

**Next:** Bookmark [QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md) for daily use!

---

## 📚 Complete Documentation Index

### For You (Corporate WSL User)
- **[START-HERE-CORPORATE.md](START-HERE-CORPORATE.md)** ← You are here
- **[QUICK-REFERENCE-CORPORATE.md](QUICK-REFERENCE-CORPORATE.md)** ← Daily commands
- **[CORPORATE-WSL-SETUP.md](CORPORATE-WSL-SETUP.md)** ← Detailed setup

### General Documentation
- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - General quick start
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [ARCHITECTURE-FIXES.md](ARCHITECTURE-FIXES.md) - Recent improvements
- [.env.example](.env.example) - Configuration options

### Deployment & Operations
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Kubernetes deployment
- [AWS-DEPLOYMENT.md](AWS-DEPLOYMENT.md) - AWS deployment
- [docs/SECURITY.md](docs/SECURITY.md) - Security practices
- [docs/SCALING.md](docs/SCALING.md) - Scaling strategies

### Troubleshooting
- [FIX-SSL-ISSUES.md](FIX-SSL-ISSUES.md) - SSL problems
- [WSL-SETUP.md](WSL-SETUP.md) - General WSL setup
- [scripts/verify-setup.sh](scripts/verify-setup.sh) - Verification script

---

**Happy coding! 🚀**
