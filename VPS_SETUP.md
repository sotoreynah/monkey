# VPS Setup Guide — Stop The Monkey

Server configuration guide for deploying on Digital Ocean.

**Target**: Ubuntu 22.04/24.04 LTS | Domain: `monkey.workez.ai`

---

## 1. Initial Server Setup

```bash
# SSH in as root
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Create app user
adduser stopmonkey
usermod -aG sudo stopmonkey

# Set up SSH key auth for new user
mkdir -p /home/stopmonkey/.ssh
cp ~/.ssh/authorized_keys /home/stopmonkey/.ssh/
chown -R stopmonkey:stopmonkey /home/stopmonkey/.ssh
chmod 700 /home/stopmonkey/.ssh
chmod 600 /home/stopmonkey/.ssh/authorized_keys

# Disable password auth
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Set timezone
timedatectl set-timezone America/New_York

# Set hostname
hostnamectl set-hostname monkey
```

## 2. Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
ufw status
```

## 3. Install Docker

```bash
# Install Docker Engine
curl -fsSL https://get.docker.com | sh

# Add user to docker group
usermod -aG docker stopmonkey

# Install Docker Compose plugin (v2)
apt install docker-compose-plugin -y

# Verify
su - stopmonkey
docker --version
docker compose version
```

## 4. DNS Configuration

Add an **A record** in your domain registrar / DNS provider:

```
Type: A
Name: monkey
Value: YOUR_DROPLET_IP
TTL: 300
```

Verify propagation:
```bash
dig monkey.workez.ai +short
# Should return your droplet IP
```

## 5. Deploy the Application

```bash
# Switch to app user
su - stopmonkey

# Clone repo
git clone https://github.com/sotoreynah/monkey.git
cd monkey

# Create environment file
cp .env.example backend/.env

# Generate a secure secret key
echo "SECRET_KEY=$(openssl rand -hex 32)" >> backend/.env

# IMPORTANT: Edit backend/.env to set your actual password
nano backend/.env
# Change ADMIN_PASSWORD=changeme to something strong

# Create data directories
mkdir -p data uploads certbot/conf certbot/www
```

## 6. Initial Boot (HTTP only, for SSL setup)

First boot without SSL to get the certbot challenge working:

```bash
# Start services
docker compose up -d --build

# Verify all containers are running
docker compose ps

# Check backend logs
docker compose logs backend

# Test: http://YOUR_DROPLET_IP should show the app
```

## 7. SSL Certificate

```bash
# Get initial certificate
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d monkey.workez.ai \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Restart nginx to pick up the cert
docker compose restart nginx

# Verify: https://monkey.workez.ai should work
```

## 8. Backup Script

```bash
# Create backup script
cat > ~/backup.sh << 'SCRIPT'
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR=~/monkey

mkdir -p $BACKUP_DIR

# Backup database
cp $APP_DIR/data/stopmonkey.db $BACKUP_DIR/stopmonkey_$DATE.db

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz $APP_DIR/uploads/ 2>/dev/null

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
SCRIPT

chmod +x ~/backup.sh

# Schedule daily at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /home/stopmonkey/backup.sh >> /home/stopmonkey/backup.log 2>&1") | crontab -

# Test it
~/backup.sh
```

## 9. Auto-Updates (Security)

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start all services | `cd ~/monkey && docker compose up -d` |
| Stop all services | `cd ~/monkey && docker compose down` |
| Rebuild after code changes | `cd ~/monkey && git pull && docker compose up -d --build` |
| View backend logs | `docker compose logs -f backend` |
| View all logs | `docker compose logs -f` |
| Manual backup | `~/backup.sh` |
| Renew SSL | `docker compose run --rm certbot renew && docker compose restart nginx` |
| Check disk space | `df -h` |
| Check running containers | `docker compose ps` |
| Access database | `docker compose exec backend python -c "import sqlite3; db=sqlite3.connect('data/stopmonkey.db'); print(db.execute('SELECT count(*) FROM transactions').fetchone())"` |

---

## Troubleshooting

**Containers won't start:**
```bash
docker compose logs    # Check for errors
docker compose down && docker compose up -d --build    # Full rebuild
```

**SSL cert expired:**
```bash
docker compose run --rm certbot renew
docker compose restart nginx
```

**Database locked:**
```bash
docker compose restart backend
```

**Out of disk space:**
```bash
docker system prune -a    # Remove unused Docker images
```
