# VPS Setup Guide — Stop The Monkey

Server configuration guide for deploying on Digital Ocean.

**Target**: Ubuntu 22.04/24.04 LTS | Domain: `monkey.workez.ai`

**Architecture**: Docker runs backend + frontend containers on localhost. The host's existing nginx reverse-proxies to them.

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
cp backend/.env backend/.env.bak   # if .env already exists
nano backend/.env
```

**Required `.env` contents:**
```
SECRET_KEY=<run: openssl rand -hex 32>
ADMIN_USERNAME=hector
ADMIN_PASSWORD=<your-strong-password>
DATABASE_URL=sqlite:///./data/stopmonkey.db
UPLOAD_DIR=./uploads
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://monkey.workez.ai,https://monkey.workez.ai
```

```bash
# Create data directories
mkdir -p data uploads

# Build and start containers
docker compose up -d --build

# Verify containers are running
docker compose ps
# Should show: monkey_backend (port 127.0.0.1:8000) and monkey_frontend (port 127.0.0.1:3000)

# Verify backend responds
curl http://127.0.0.1:8000/api/health
# Expected: {"status":"ok","app":"Stop The Monkey"}

# Verify frontend responds
curl -s http://127.0.0.1:3000 | head -5
# Expected: HTML content
```

## 6. Configure Host Nginx (Reverse Proxy)

Since the VPS already runs nginx for other sites, we add a site config for monkey:

```bash
# Create site config
sudo nano /etc/nginx/sites-available/monkey.workez.ai
```

Paste the following:

```nginx
server {
    listen 80;
    server_name monkey.workez.ai;

    client_max_body_size 10M;

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/monkey.workez.ai /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Test from outside (or browser)
curl http://monkey.workez.ai/api/health
```

## 7. SSL Certificate

```bash
# Use certbot with the host nginx plugin
sudo certbot --nginx -d monkey.workez.ai

# Certbot will:
#   1. Obtain a Let's Encrypt certificate
#   2. Auto-modify the nginx config to add SSL directives
#   3. Set up auto-renewal

# Verify HTTPS works
curl https://monkey.workez.ai/api/health
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

| Action                     | Command                                                                                                                                                               |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Start all services         | `cd ~/monkey && docker compose up -d`                                                                                                                                 |
| Stop all services          | `cd ~/monkey && docker compose down`                                                                                                                                  |
| Rebuild after code changes | `cd ~/monkey && git pull && docker compose up -d --build`                                                                                                             |
| View backend logs          | `docker compose logs -f backend`                                                                                                                                      |
| View all logs              | `docker compose logs -f`                                                                                                                                              |
| Manual backup              | `~/backup.sh`                                                                                                                                                         |
| Renew SSL                  | `sudo certbot renew`                                                                                                                                                  |
| Check disk space           | `df -h`                                                                                                                                                               |
| Check running containers   | `docker compose ps`                                                                                                                                                   |
| Reload host nginx          | `sudo systemctl reload nginx`                                                                                                                                         |
| Access database            | `docker compose exec backend python -c "import sqlite3; db=sqlite3.connect('data/stopmonkey.db'); print(db.execute('SELECT count(*) FROM transactions').fetchone())"` |

---

## Troubleshooting

**Containers won't start:**
```bash
docker compose logs    # Check for errors
docker compose down && docker compose up -d --build    # Full rebuild
```

**Port conflict (address already in use):**
```bash
# Check what's using a port
sudo lsof -i :8000
sudo lsof -i :3000
# The containers bind to 127.0.0.1 only, so they shouldn't conflict with nginx on 80/443
```

**SSL cert expired:**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

**Database locked:**
```bash
docker compose restart backend
```

**Out of disk space:**
```bash
docker system prune -a    # Remove unused Docker images
```

**Host nginx not proxying:**
```bash
# Check if site is enabled
ls -la /etc/nginx/sites-enabled/monkey.workez.ai

# Test nginx config
sudo nginx -t

# Check nginx error log
sudo tail -50 /var/log/nginx/error.log
```
