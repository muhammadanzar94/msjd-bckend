#!/usr/bin/env bash
# Run once on a fresh Ubuntu 22.04 VM, before cloning the app repos.
# Usage: DB_PASSWORD='choose-a-strong-password' bash provision-vm.sh
set -euo pipefail

: "${DB_PASSWORD:?Set DB_PASSWORD env var first, e.g. DB_PASSWORD=xxx bash provision-vm.sh}"

echo "== Updating system =="
sudo apt-get update && sudo apt-get upgrade -y

echo "== Installing Python, MySQL, nginx, certbot, ffmpeg =="
sudo apt-get install -y python3 python3-venv python3-pip python3-dev \
    default-libmysqlclient-dev pkg-config build-essential \
    mysql-server nginx certbot python3-certbot-nginx git ffmpeg

echo "== Installing Node.js 22 LTS =="
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "== Creating the app database =="
sudo mysql -e "CREATE DATABASE IF NOT EXISTS msjd_db CHARACTER SET utf8mb4;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'msjd_user'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';"
sudo mysql -e "GRANT ALL PRIVILEGES ON msjd_db.* TO 'msjd_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "== Tuning MySQL for a 1GB RAM VM =="
sudo tee /etc/mysql/mysql.conf.d/low-memory.cnf > /dev/null <<'EOF'
[mysqld]
innodb_buffer_pool_size = 128M
performance_schema = off
max_connections = 30
EOF
sudo systemctl restart mysql

echo "== Adding a 1GB swapfile (safety margin on a 1GB RAM VM) =="
if [ ! -f /swapfile ]; then
    sudo fallocate -l 1G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "== Done. Next: clone both repos into \$HOME, add .env files, then run deploy/app-setup.sh =="
