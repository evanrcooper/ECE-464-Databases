#!/bin/bash
set -e

# Check if the database directory is empty
if [ -z "$(ls -A /var/lib/postgresql/data 2>/dev/null)" ]; then
    echo "Initializing database..."
    initdb -D /var/lib/postgresql/data
else
    echo "Database already initialized."
fi
