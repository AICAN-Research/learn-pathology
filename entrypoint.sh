#!/bin/sh

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser
echo "Create superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
username = '$DJANGO_SUPERUSER_USERNAME'
if not U.objects.filter(username=username).exists():
    U.objects.create_superuser(
        username,
        '$DJANGO_SUPERUSER_EMAIL',
        '$DJANGO_SUPERUSER_PASSWORD',
    )
"

# Start server
exec python manage.py runserver 0.0.0.0:8000