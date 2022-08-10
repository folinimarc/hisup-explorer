#!/bin/bash --login
set -e
conda activate $ENV_PREFIX

#redis-server
celery -A footprint_service worker -l info --detach
celery -A footprint_service flower
