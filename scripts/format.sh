#!/bin/bash
# Format Python code using black

set -e

echo "Running black formatter..."
uv run black backend/

echo "Format complete!"
