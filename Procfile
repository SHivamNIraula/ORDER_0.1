release: python manage.py migrate --settings=order_mng.production_settings
web: daphne -b 0.0.0.0 -p $PORT order_mng.asgi:application