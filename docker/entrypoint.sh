#!/bin/sh
# Apply migrations and collect static files, then hand off to the CMD.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput --verbosity 0

if [ "${SEED_ON_START:-false}" = "true" ]; then
  python manage.py seed_data --demo-users
fi

exec "$@"
