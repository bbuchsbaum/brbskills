#!/bin/sh
# Fixture-only rendered batch payload. The Python payload retains argv as an array.
exec python3 "$(dirname "$0")/payload.py"
