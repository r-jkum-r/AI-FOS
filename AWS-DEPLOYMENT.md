# AWS Deployment Guide

## Quick AWS Setup (30 Minutes)

This guide shows you how to deploy the AI Voice Translation system on AWS EC2.

## Step 1: Launch EC2 Instance

### 1.1 Login to AWS Console
- Go to: https://console.aws.amazon.com/
- Navigate to: EC2 → Instances → Launch Instance

### 1.2 Choose Instance Configuration

**Name:** `voice-agent-server`

**AMI (Operating System):**
- Ubuntu Server 22.04 LTS (Free tier eligible)
- 64-bit (x86)

**Instance Type:**
Choose based on your needs:

| Use Case | Instance Type | vCPU | RAM | Cost/Month* |
|----------|--------------|------|-----|-------------|
| Testing | t3.large | 2 | 8GB | ~$60 |
| Production (50 calls) | t3.xlarge | 4 | 16GB | ~$120 |
| Production (200 calls) | t3.2xlarge | 8 | 32GB | ~$240 |
| GPU Accelerated | g4dn.xlarge | 4 | 16GB + GPU | ~$380 |

*Approximate costs, check AWS pricing

**Recommended for starting:** `t3.xlarge` (4 vCPU, 16GB RAM)

### 1.3 Configure Storage
- Root volume: 100 GB (gp3)
- This stores the OS, Docker images, and AI models

### 1.4 Configure Security Group

Create a new security group with these rules:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | SSH access |
| HTTP | TCP | 8000 | 0.0.0.0/0 | API access |
| Custom UDP | UDP | 5060 | 0.0.0.0/0 | SIP signaling |
| Custom TCP | TCP | 5060 | 0.0.0.0/0 | SIP signaling |
| Custom UDP | UDP | 10000-10100 | 0.0.0.0/0 | RTP audio |
| HTTP | TCP | 3000 | Your IP | Grafana dashboard |
| HTTP | TCP | 9090 | Your IP | Prometheus |

**Important:** Replace "Your IP" with your actual IP address for security.

### 1.5 Create/Select Key Pair
- Create new key pair: `voice-agent-key`
- Download the `.pem` file
- Save it securely (you'll need it to connect)

### 1.6 Launch Instance
- Click "Launch Instance"
- Wait 2-3 minutes for instance to start

## Step 2: Connect to Your Instance

### 2.1 Get Instance Details
```bash
# In AWS Console, note down:
# - Public IPv4 address (e.g., 54.123.45.67)
# - Public IPv4 DNS (e.g., ec2-54-123-45-67.compute-1.amazonaws.com)
```

### 2.2 Connect via SSH

**On Linux/Mac:**
```bash
# Set correct permissions for key file
chmod 400 voice-agent-key.pem

# Connect to instance
ssh -i voice-agent-key.pem ubuntu@YOUR_PUBLIC_IP

# Example:
# ssh -i voice-agent-key.pem ubuntu@54.123.45.67
```

**On Windows:**
- Use PuTTY or Windows Terminal with SSH
- Or use AWS Console → Connect → EC2 Instance Connect

## Step 3: Install Docker on EC2

Once connected via SSH, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install docker-compose -y

# Install git
sudo apt install git -y

# Logout and login again for group changes
exit
```

**Reconnect via SSH:**
```bash
ssh -i voice-agent-key.pem ubuntu@YOUR_PUBLIC_IP
```

**Verify installation:**
```bash
docker --version
docker-compose --version
```

## Step 4: Deploy the Application

```bash
# Clone the repository
git clone <your-repo-url>
cd voice-ai-agent

# Update Asterisk configuration with your public IP
export PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)
echo "Your public IP: $PUBLIC_IP"

# Update sip.conf with public IP
sed -i "s/YOUR_PUBLIC_IP/$PUBLIC_IP/g" asterisk/sip.conf

# Start all services
docker-compose up -d

# This will take 10-15 minutes first time (downloading models)
# Watch the progress:
docker-compose logs -f backend
```

**Wait for this message:**
```
INFO: Application startup complete.
```

Press `Ctrl+C` to exit logs.

## Step 5: Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Should show all services as "Up"

# Test the API
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"voice-gateway"}
```

## Step 6: Test from Your Phone

### 6.1 Install Linphone App
- Android: Google Play Store
- iPhone: Apple App Store

### 6.2 Configure SIP Account in Linphone

**Settings:**
- Username: `test-user`
- Password: (leave blank)
- Domain: `YOUR_EC2_PUBLIC_IP:5060`
- Transport: UDP

**Example:**
- Domain: `54.123.45.67:5060`

### 6.3 Make Test Call
1. Dial: `1000`
2. Speak in Tamil/Telugu/Hindi
3. Listen for Hinglish translation

## Step 7: Access Monitoring Dashboards

**Grafana (Statistics Dashboard):**
```
http://YOUR_EC2_PUBLIC_IP:3000
Username: admin
Password: admin
```

**Prometheus (Metrics):**
```
http://YOUR_EC2_PUBLIC_IP:9090
```

## AWS-Specific Optimizations

### Enable Elastic IP (Recommended)

Elastic IP gives you a permanent IP address:

```bash
# In AWS Console:
# 1. EC2 → Elastic IPs → Allocate Elastic IP
# 2. Actions → Associate Elastic IP address
# 3. Select your instance
# 4. Associate
```

Benefits:
- IP doesn't change when you restart instance
- No need to reconfigure SIP clients

### Setup Auto-Scaling (For Production)

For handling variable call loads:

1. Create AMI from your configured instance
2. Create Launch Template
3. Create Auto Scaling Group
4. Set scaling policies based on CPU/Memory

See: [docs/SCALING.md](docs/SCALING.md)

### Use AWS EFS for Model Storage

To share models across multiple instances:

```bash
# Create EFS filesystem in AWS Console
# Mount it to /models
sudo apt install nfs-common -y
sudo mount -t nfs4 -o nfsvers=4.1 fs-xxxxx.efs.region.amazonaws.com:/ /models
```

### Enable CloudWatch Monitoring

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure monitoring
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## Cost Optimization

### 1. Use Spot Instances (Save 70%)
- Good for non-critical workloads
- Can be interrupted by AWS

### 2. Use Reserved Instances (Save 40%)
- Commit to 1-3 years
- Good for production

### 3. Stop Instance When Not Needed
```bash
# Stop instance (keeps data, stops billing for compute)
aws ec2 stop-instances --instance-ids i-xxxxx

# Start instance
aws ec2 start-instances --instance-ids i-xxxxx
```

### 4. Use Smaller Instance for Testing
- Start with t3.large for testing
- Scale up to t3.xlarge for production

## Backup Strategy

### Manual Backup
```bash
# Create AMI snapshot
# AWS Console → EC2 → Instances → Actions → Image → Create Image
```

### Automated Backup
```bash
# Create backup script
cat > /home/ubuntu/backup.sh << 'EOF'
#!/bin/bash
docker-compose exec redis redis-cli BGSAVE
aws s3 sync /var/lib/docker/volumes s3://your-backup-bucket/
EOF

chmod +x /home/ubuntu/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup.sh
```

## Security Hardening

### 1. Update Security Group
```bash
# Restrict SSH to your IP only
# AWS Console → EC2 → Security Groups → Edit inbound rules
# SSH (22) → Source: My IP
```

### 2. Enable AWS WAF
- Protects against DDoS attacks
- Rate limiting for API endpoints

### 3. Use AWS Secrets Manager
```bash
# Store sensitive credentials
aws secretsmanager create-secret \
  --name voice-agent/asterisk \
  --secret-string '{"username":"asterisk","password":"STRONG_PASSWORD"}'
```

### 4. Enable VPC Flow Logs
- Monitor network traffic
- Detect suspicious activity

## Troubleshooting

### Can't connect via SSH
```bash
# Check security group allows SSH from your IP
# Check instance is running
# Check key file permissions: chmod 400 voice-agent-key.pem
```

### Can't make SIP calls
```bash
# Check security group allows UDP 5060 and 10000-10100
# Verify public IP in sip.conf:
cat asterisk/sip.conf | grep external

# Should show your EC2 public IP
```

### High costs
```bash
# Check instance type
aws ec2 describe-instances --instance-ids i-xxxxx

# Consider downsizing or using spot instances
```

### Out of disk space
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a

# Or increase EBS volume size in AWS Console
```

## Production Checklist

- [ ] Use t3.xlarge or larger instance
- [ ] Allocate Elastic IP
- [ ] Configure proper security groups
- [ ] Enable CloudWatch monitoring
- [ ] Setup automated backups
- [ ] Configure auto-scaling
- [ ] Enable SSL/TLS for API
- [ ] Setup domain name (Route 53)
- [ ] Configure log rotation
- [ ] Test disaster recovery

## Monitoring Commands

```bash
# Check system resources
htop

# Check Docker stats
docker stats

# Check active calls
curl http://localhost:8000/stats

# Check logs
docker-compose logs -f

# Check Asterisk status
docker-compose exec asterisk asterisk -rx "core show channels"
```

## Useful AWS CLI Commands

```bash
# Install AWS CLI
sudo apt install awscli -y

# Configure AWS CLI
aws configure

# List your instances
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]' --output table

# Stop instance
aws ec2 stop-instances --instance-ids i-xxxxx

# Start instance
aws ec2 start-instances --instance-ids i-xxxxx

# Create snapshot
aws ec2 create-snapshot --volume-id vol-xxxxx --description "voice-agent-backup"
```

## Next Steps

1. **Test thoroughly** with multiple concurrent calls
2. **Monitor performance** via Grafana
3. **Setup alerts** for high CPU/memory usage
4. **Configure domain name** for easier access
5. **Enable HTTPS** for API endpoints
6. **Setup CI/CD** for automated deployments

## Support Resources

- AWS Documentation: https://docs.aws.amazon.com/
- AWS Support: https://console.aws.amazon.com/support/
- Project Documentation: [docs/](docs/)
- Architecture Guide: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)


## Automated Deployment with Terraform (Advanced)

If you prefer automated infrastructure setup:

### Install Terraform

```bash
# On your local machine
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform --version
```

### Deploy with Terraform

```bash
# Navigate to terraform directory
cd infra/terraform

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars

# Edit these values:
# - key_name: Your AWS key pair name
# - allowed_ssh_cidr: Your IP address (for security)

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply

# Terraform will output:
# - Instance ID
# - Public IP
# - SSH command
# - API URL
# - Grafana URL
```

### Connect and Deploy Application

```bash
# Use the SSH command from terraform output
ssh -i your-key.pem ubuntu@TERRAFORM_OUTPUT_IP

# Clone and deploy
git clone <your-repo-url>
cd voice-ai-agent

# Update Asterisk config with public IP
export PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)
sed -i "s/YOUR_PUBLIC_IP/$PUBLIC_IP/g" asterisk/sip.conf

# Start services
docker-compose up -d
```

### Destroy Infrastructure (When Done)

```bash
# From your local machine in infra/terraform/
terraform destroy
```

This will delete all AWS resources and stop billing.
