#!/bin/bash

# Memory Trainer Runner
# Uses the specified Python environment: ~/atlassian/src/ml-studio/ml_3.11

PYTHON_ENV="~/atlassian/src/ml-studio/ml_3.11/bin/python"

# Expand the tilde to full path
PYTHON_PATH="${PYTHON_ENV/#\~/$HOME}"

echo "Using Python environment: $PYTHON_PATH"
echo "Python version: $($PYTHON_PATH --version)"
echo "Starting Memory Trainer..."
echo ""

# Run the trainer
exec "$PYTHON_PATH" trainer.py