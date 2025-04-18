#!/usr/bin/env bash

set -e  # Exit on error
set -x  # Print commands

# Shut down everything cleanly (remove volumes too if needed)
docker compose down --remove-orphans

# Optional: wipe DB volume if you want a clean slate
# docker volume rm yourprojectname_postgres_data

# Rebuild containers
docker compose build

# Start containers (detached)
docker compose up -d --wait

# Optionally attach logs
# docker compose logs -f
