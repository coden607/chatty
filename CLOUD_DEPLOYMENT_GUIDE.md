# CHATTY Cloud Deployment Guide

Complete guide for deploying CHATTY automation system to various cloud providers for 24/7 operation.

---

## Quick Comparison

| Provider | Free Tier | 24/7 Free? | Best For |
|----------|-----------|------------|----------|
| **Oracle Cloud** | Always Free (4 ARM VMs) | ✅ Yes | Production, maximum free resources |
| **Google Cloud** | $300 credit + e2-micro | ✅ Yes (with limits) | Familiarity with GCP |
| **AWS** | 12 months free t2.micro | ✅ Yes (first year) | Enterprise features |
| **Railway** | $5/month credit | ⚠️ ~500 hours/month | Easy deployment |
| **Render** | Web services free | ❌ No (sleeps after 15min) | Simple web apps |
| **Fly.io** | $5/month credit | ⚠️ Limited | Edge deployment |

---

## Recommended: Oracle Cloud (Always Free)

Oracle Cloud offers the best free tier with genuinely always-free resources that never expire.

### What's Included (Always Free)
- **4 ARM-based Ampere A1 VMs** (up to 4 OCPUs, 24 GB RAM total)
- **2 AMD-based VMs** (1/8 OCPU, 1 GB RAM each)
- **10 TB/month** data transfer
- **200 GB** block storage

### Deployment Steps

#### 1. Create Oracle Cloud Account
1. Go to https://www.oracle.com/cloud/free/
2. Sign up with email and credit card (for verification, not charged)
3. Complete registration

#### 2. Run Deployment Script
```bash
cd ~/Projects/chatty
chmod +x deploy-oracle-cloud.sh
./deploy-oracle-cloud.sh
```

This will:
- Install OCI CLI if needed
- Create an ARM-based VM (2 OCPUs, 12GB RAM)
- Configure SSH access
- Set up Docker
- Provide connection details

#### 3. Manual Setup (if script fails)

**Create VM via Console:**
1. Go to https://cloud.oracle.com/compute/instances
2. Click "Create Instance"
3. Name: `chatty-automation`
4. Shape: `VM.Standard.A1.Flex` (ARM)
5. OCPUs: 2, Memory: 12 GB
6. Image: Oracle Linux 9
7. Add your SSH public key
8. Create

**SSH and Setup:**
```bash
ssh -i ~/.ssh/your_key opc@YOUR_VM_IP

# Install Docker
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone CHATTY
git clone <your-repo> /opt/chatty
cd /opt/chatty

# Copy your .env file (from local machine)
scp -i ~/.ssh/your_key .env opc@YOUR_VM_IP:/opt/chatty/.env

# Start CHATTY
docker-compose up -d
```

---

## Alternative: Google Cloud Platform

### Free Tier
- **e2-micro** instance (US regions only) - always free
- 1 GB memory, shared vCPU
- 30 GB-months standard persistent disks
- 1 GB network egress

### Deployment

```bash
# Install gcloud CLI
https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Create VM
gcloud compute instances create chatty-server \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=30GB \
    --tags=http-server,https-server

# SSH and setup (similar to Oracle)
gcloud compute ssh chatty-server --zone=us-central1-a
```

---

## Alternative: Railway (Easiest)

Railway offers the simplest deployment experience.

### Free Tier
- $5 credit per month (~500 hours)
- Good for testing and development
- Upgrade to Hobby ($5/month) for 24/7

### Deployment
```bash
cd ~/Projects/chatty
chmod +x deploy-railway.sh
./deploy-railway.sh
```

Or manually:
```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

# Initialize and deploy
railway init --name chatty-automation
railway up
```

---

## Monitoring Your Deployment

### Check Service Status
```bash
# SSH into your server
ssh opc@YOUR_SERVER_IP

# Check CHATTY status
cd /opt/chatty && docker-compose ps

# View logs
docker-compose logs -f chatty-continuous

# Check system resources
htop
df -h
free -m
```

### Setup Alerts (Oracle Cloud)
1. Go to Monitoring → Alarm Definitions
2. Create alarms for:
   - High CPU usage (>80%)
   - Low disk space (<20%)
   - Instance health check failures

---

## Keeping CHATTY Running 24/7

### Auto-Restart on Boot
```bash
# On the server, ensure Docker starts on boot
sudo systemctl enable docker

# In docker-compose.yml, services already have:
# restart: unless-stopped
```

### Health Checks
CHATTY includes built-in health monitoring:
- API health endpoint: `http://YOUR_IP:8000/health`
- Automatic component restart
- Key rotation every 5 minutes
- Metrics collection every 10 minutes

### Backup Strategy
```bash
# Create backup script
cat > /opt/chatty/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backups/$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker cp chatty-continuous:/app/data/chatty.db $BACKUP_DIR/

# Backup generated content
cp -r /opt/chatty/generated_content $BACKUP_DIR/

# Backup logs
cp -r /opt/chatty/logs $BACKUP_DIR/

# Compress
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# Keep only last 7 days
find /backups -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/chatty/backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /opt/chatty/backup.sh" | sudo crontab -
```

---

## Troubleshooting

### VM Runs Out of Memory
```bash
# Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Docker Containers Won't Start
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d

# Rebuild if needed
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### API Keys Not Working
```bash
# SSH to server and verify env vars
docker exec chatty-continuous env | grep API_KEY

# Update .env and restart
docker-compose down
docker-compose up -d
```

---

## Security Best Practices

1. **Use SSH Keys Only** - Disable password authentication
2. **Firewall Rules** - Only open necessary ports (22, 8000)
3. **Regular Updates** - Keep system and Docker images updated
4. **Secrets Management** - Never commit .env files
5. **Monitor Logs** - Regularly check for suspicious activity

---

## Cost Optimization

### Oracle Cloud (Always Free)
- ✅ No charges if staying within always-free limits
- Monitor usage at: https://cloud.oracle.com/usage

### Other Providers
- Set up billing alerts
- Use spot instances where available
- Right-size your VMs
- Consider auto-shutdown for non-production

---

## Next Steps

Once deployed:
1. **Enable auto-start**: `sudo systemctl enable docker`
2. **Setup monitoring**: Configure alerts for health checks
3. **Test failover**: Verify API key rotation works
4. **Schedule backups**: Daily automated backups
5. **Document access**: Save SSH keys and IP addresses securely

For help, check logs:
```bash
docker-compose logs -f --tail=100
```
