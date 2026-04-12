# EduPath — VPS Deploy Qo'llanmasi
# Ubuntu 22.04 | Nginx | Gunicorn | PostgreSQL | Redis

## 1. Server sozlash
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx postgresql redis-server certbot python3-certbot-nginx
```

## 2. PostgreSQL
```bash
sudo -u postgres psql
CREATE DATABASE edupath_db;
CREATE USER edupath_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE edupath_db TO edupath_user;
\q
```

## 3. Loyihani yuklash
```bash
cd /var/www
git clone https://github.com/yourname/edupath.git
cd edupath
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. .env yaratish
```bash
cp .env.example .env
nano .env   # o'zingizning qiymatlaringizni kiriting
```

## 5. Django sozlash
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 6. Gunicorn systemd service
```ini
# /etc/systemd/system/edupath.service
[Unit]
Description=EduPath Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/edupath
ExecStart=/var/www/edupath/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/edupath.sock \
    edupath.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable edupath
sudo systemctl start edupath
```

## 7. Celery systemd service
```ini
# /etc/systemd/system/edupath-celery.service
[Unit]
Description=EduPath Celery Worker
After=network.target redis.service

[Service]
User=www-data
WorkingDirectory=/var/www/edupath
ExecStart=/var/www/edupath/venv/bin/celery -A edupath worker -l info
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable edupath-celery
sudo systemctl start edupath-celery
```

## 8. Nginx konfiguratsiyasi
```nginx
# /etc/nginx/sites-available/edupath
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /var/www/edupath/staticfiles/;
    }

    location /media/ {
        alias /var/www/edupath/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/edupath.sock;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/edupath /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 9. SSL (HTTPS bepul)
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Tekshirish
```bash
sudo systemctl status edupath
sudo systemctl status edupath-celery
sudo journalctl -u edupath -f
```
