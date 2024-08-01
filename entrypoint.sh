#!/bin/sh
set -e

# activate venv
. /app/venv/bin/activate

# excecute main.py with shell arguments
python3 /app/main.py "$@"
