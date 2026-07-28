#!/usr/bin/env bash
# Run from $HOME after provision-vm.sh, after cloning both repos into
# ~/masjid and ~/msjd-frontend, and after creating both .env files.
set -euo pipefail

USER_NAME="$(whoami)"
BACKEND_DIR="$HOME/masjid"
FRONTEND_DIR="$HOME/msjd-frontend"

echo "== Django: venv + deps + migrate + collectstatic =="
cd "$BACKEND_DIR"
python3.12 -m venv venv
# Call the venv's binaries directly rather than `source activate` — activate
# is meant for interactive shells; calling by path is the robust pattern
# for scripts and can't silently fall through to the system Python.
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
venv/bin/python manage.py migrate
venv/bin/python manage.py collectstatic --noinput

echo "== Next.js: install + build =="
cd "$FRONTEND_DIR"
npm install
npm run build

echo "== Installing systemd services =="
sed "s/__USER__/$USER_NAME/g" "$BACKEND_DIR/deploy/gunicorn.service" | sudo tee /etc/systemd/system/gunicorn.service > /dev/null
sed "s/__USER__/$USER_NAME/g" "$FRONTEND_DIR/deploy/nextjs.service" | sudo tee /etc/systemd/system/nextjs.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn nextjs

echo "== Installing nginx config =="
sed "s/__USER__/$USER_NAME/g" "$BACKEND_DIR/deploy/nginx.conf" | sudo tee /etc/nginx/sites-available/msjid > /dev/null
sudo ln -sf /etc/nginx/sites-available/msjid /etc/nginx/sites-enabled/msjid
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo "== Done. Check status with: sudo systemctl status gunicorn nextjs nginx =="
