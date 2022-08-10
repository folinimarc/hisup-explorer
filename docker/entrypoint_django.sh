#!/bin/bash --login
set -e
conda activate $ENV_PREFIX

# collect static files
python manage.py collectstatic --no-input
# make and apply migrations
python manage.py makemigrations
python manage.py migrate
# create superuser
export DJANGO_SUPERUSER_EMAIL=foo@bar.com
export DJANGO_SUPERUSER_USERNAME=foobar
export DJANGO_SUPERUSER_PASSWORD=foobar
python manage.py createsuperuser --noinput

# start django
gunicorn --workers 2 --threads 2 --bind 0.0.0.0:8000 main.wsgi
