#!/bin/bash --login
set -e
conda activate $ENV_PREFIX

# apply migrations
python manage.py migrate
# collect static files
python manage.py collectstatic --no-input

# start django
gunicorn --workers 2 --threads 4 --bind 0.0.0.0:8000 main.wsgi
