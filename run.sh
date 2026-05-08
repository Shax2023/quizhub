#!/bin/bash
cd "$(dirname "$0")"

export DJANGO_SETTINGS_MODULE=quiz_project.settings
export PORT=${PORT:-5000}

python3 manage.py migrate --noinput 2>&1

python3 manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@quizhub.uz', 'admin123')
    print('Superuser created: admin / admin123')
" 2>&1

python3 manage.py seed_data 2>&1

python3 manage.py collectstatic --noinput -v 0 2>&1

exec python3 manage.py runserver 0.0.0.0:${PORT} --noreload
