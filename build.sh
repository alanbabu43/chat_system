#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python chat_system/manage.py collectstatic --no-input
python chat_system/manage.py migrate
