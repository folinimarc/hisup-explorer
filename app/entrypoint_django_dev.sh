#!/bin/bash --login
set -e
conda activate $ENV_PREFIX

# apply migrations
python manage.py migrate

# start django
python manage.py runserver 0.0.0.0:8000
