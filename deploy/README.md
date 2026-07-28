# Deploying Msjd to GCP on minimum resources

One `e2-micro` Compute Engine VM (GCP's Always Free tier), running Django,
MySQL, and Next.js together, behind nginx. No Cloud SQL (never free), no
Cloud Run split-services — just one VM. Total cost: ~$0/month compute,
just your domain (~$10–15/year).

Files referenced below:
- `masjid/deploy/provision-vm.sh` — installs system packages (run once)
- `masjid/deploy/app-setup.sh` — builds both apps + installs services (run once, and again after each `git pull`)
- `masjid/deploy/gunicorn.service`, `msjd-frontend/deploy/nextjs.service` — systemd units
- `masjid/deploy/nginx.conf` — reverse proxy config
- `masjid/deploy/env.production.example`, `msjd-frontend/deploy/env.production.example` — env var templates

## 1. Create the GCP project

In the browser: console.cloud.google.com → create a new project → enable
billing on it (required even for free-tier usage — you won't be charged as
long as you stay within Always Free limits and use one of the three free
regions below).

Then either install the `gcloud` CLI locally and run `gcloud init` +
`gcloud auth login`, or just open **Cloud Shell** (the `>_` icon in the
console) — it comes with `gcloud` pre-installed and pre-authenticated, no
local setup needed. Everything below can be run from Cloud Shell.

```bash
gcloud config set project YOUR_PROJECT_ID
```

## 2. Reserve a static IP, then create the VM

Reserve the IP first so it doesn't change if the VM restarts (a changing IP
would break your DNS records).

```bash
# us-west1, us-central1, or us-east1 — only these three are Always Free
gcloud compute addresses create msjid-ip --region=us-central1

gcloud compute instances create msjid-vm \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --address=msjid-ip \
  --tags=http-server,https-server

gcloud compute firewall-rules create allow-http --allow=tcp:80 --target-tags=http-server
gcloud compute firewall-rules create allow-https --allow=tcp:443 --target-tags=https-server

# Note this down — you'll point DNS at it
gcloud compute addresses describe msjid-ip --region=us-central1 --format='get(address)'
```

## 3. Domain — or skip it for now with nip.io

**No domain yet?** Use [nip.io](https://nip.io) — free wildcard DNS with
zero setup. `anything.<your-ip-with-dots-replaced-by-dashes>.nip.io`
resolves straight to that IP. If your static IP from step 2 is
`34.123.45.67`, then both `34-123-45-67.nip.io` (the bare app) and
`masjid-noor.34-123-45-67.nip.io` (a mosque's public page) resolve
correctly — the full subdomain-based multi-tenant experience works exactly
as it will with a real domain, no DNS records to create at all. This is
what `BASE_DOMAIN` gets set to in step 5.

Skip straight to step 4.

**Have a domain?** At your registrar / DNS provider, add:

| Type | Name | Value |
|---|---|---|
| A | `@` | the static IP from step 2 |
| A | `*` | the static IP from step 2 |

The wildcard (`*`) record is what makes `<masjid-slug>.yourdomain.com`
resolve for every mosque. DNS can take a few minutes to a few hours to
propagate.

## 4. SSH in and provision

```bash
gcloud compute ssh msjid-vm --zone=us-central1-a
```

Then on the VM:

```bash
git clone https://github.com/muhammadanzar94/msjd-bckend.git masjid
git clone https://github.com/muhammadanzar94/msjd-frontend.git msjd-frontend

DB_PASSWORD='choose-a-strong-password' bash masjid/deploy/provision-vm.sh
```

## 5. Configure environment variables

```bash
cp masjid/deploy/env.production.example masjid/.env
nano masjid/.env   # fill in DB_PASSWORD (from step 4), SECRET_KEY, and
                    # BASE_DOMAIN/ALLOWED_HOSTS (nip.io host or real domain — see the comment in the file)

cp msjd-frontend/deploy/env.production.example msjd-frontend/.env.local
nano msjd-frontend/.env.local   # same BASE_DOMAIN value
```

Generate a real `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

(`nginx.conf` doesn't need editing — it's a catch-all that works for IP,
nip.io, or a real domain without changes.)

## 6. Build and start everything

```bash
bash masjid/deploy/app-setup.sh
```

This builds both apps, installs the systemd services, and starts nginx.
At this point the app is live over plain HTTP at your static IP directly,
or at `http://<BASE_DOMAIN>` if you set up nip.io or a real domain (no SSL
yet — see step 8).

Check status any time:

```bash
sudo systemctl status gunicorn nextjs nginx
sudo journalctl -u gunicorn -f     # tail Django logs
sudo journalctl -u nextjs -f       # tail Next.js logs
```

## 7. Create your first system admin

```bash
cd ~/masjid && source venv/bin/activate
python manage.py createsuperuser
deactivate
```

(Automatically gets `role=system_admin` — see `users/models.py`.)

## 8. SSL (wildcard cert) — needs a real domain

This step requires owning a real domain — you can't get a wildcard cert
for a nip.io hostname (you don't control its DNS, which the challenge
below needs) or a bare IP. Totally fine to stay on plain HTTP while
testing on nip.io/IP and come back to this once you've bought a domain
and repointed DNS per step 3.

Let's Encrypt requires a **DNS-01** challenge for wildcard certs (the
simpler HTTP-01 challenge only covers a single domain, not `*.yourdomain.com`).

**If your DNS is on Cloudflare** (free, and automates renewal too):

```bash
sudo apt-get install -y python3-certbot-dns-cloudflare
mkdir -p ~/.secrets && echo "dns_cloudflare_api_token = YOUR_CF_API_TOKEN" > ~/.secrets/cloudflare.ini
chmod 600 ~/.secrets/cloudflare.ini
sudo certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
  -d yourdomain.com -d '*.yourdomain.com'
```

**Any other DNS provider** (manual — you'll repeat this every ~90 days):

```bash
sudo certbot certonly --manual --preferred-challenges dns \
  -d yourdomain.com -d '*.yourdomain.com'
# Certbot prints a TXT record to add at your DNS provider. Add it, wait a
# minute, then press Enter.
```

Either way, once you have a cert, add this to the top of the `server`
block in `/etc/nginx/sites-available/msjid` (`sudo nano ...`), and change
the existing `listen 80;` line to redirect instead of serve:

```nginx
server {
    listen 80;
    server_name yourdomain.com *.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com *.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # ...keep everything else from the original server block (client_max_body_size,
    # the /media/, /static/, /admin|api/, and / location blocks) unchanged here...
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## Notes on the 1GB RAM tradeoff

`provision-vm.sh` adds a 1GB swapfile and tunes MySQL's buffer pool down —
enough headroom for this project's actual scale (a handful of mosques,
tens of concurrent users). If you outgrow it, the first thing to bump is
the machine type (`gcloud compute instances set-machine-type msjid-vm
--machine-type=e2-small`, VM must be stopped first) — that leaves the free
tier and starts costing a few dollars/month, but everything else in this
setup stays the same.

## Redeploying after code changes

```bash
cd ~/masjid && git pull && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput && deactivate && sudo systemctl restart gunicorn

cd ~/msjd-frontend && git pull && npm install && npm run build && sudo systemctl restart nextjs
```
