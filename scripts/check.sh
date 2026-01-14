#!/bin/bash
# Check code quality without making changes

set -e

echo "Checking code formatting with black..."
uv run black --check --diff backend/

echo "All checks passed!"
