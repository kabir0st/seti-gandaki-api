#!/bin/bash

LOCKFILE="/app/entrypoint_lock"

if [ -f "$LOCKFILE" ]; then
    echo "Entrypoint already executed. Skipping initial setup tasks."
else
    echo "Running initial setup tasks for the first time..."
    # Check for unapplied migrations
    python3 manage.py shell < wait_for_db.py
    echo "Checking for unapplied migrations..."
    UNAPPLIED_MIGRATIONS=$(python3 manage.py showmigrations --plan | grep '\[ \]' | wc -l)

    if [ "$UNAPPLIED_MIGRATIONS" -gt 0 ]; then
        echo "Unapplied migrations detected, running migrations and seeders..."
        python3 manage.py makemigrations system 
        python3 manage.py migrate
        python3 manage.py flush --no-input
        python3 manage.py populate_users
        python3 manage.py populate_inventory  
        python3 manage.py initialize_buckets
        python3 manage.py collectstatic --noinput
    else
        echo "All migrations are applied, skipping migration and seeding."
    fi
    # Create a lock file to prevent reruns
    touch "$LOCKFILE"
fi
# Start the Django development server
exec "$@"
