#!/bin/bash --login
set -e
conda activate $ENV_PREFIX

# Copy nginx conf explicity to shared volume
rm -f /home/app/nginx_mount/default.conf
cp /home/app/nginx/nginx.conf /home/app/nginx_mount/

# apply migrations
python manage.py migrate
# collect static files
python manage.py collectstatic --no-input

# start django
gunicorn --workers 2 --threads 4 --bind 0.0.0.0:8000 main.wsgi
