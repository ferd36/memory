#!/bin/bash

# Memory Trainer Pygame Runner
# Uses the specified Python environment: ~/atlassian/src/ml-studio/ml_3.11

PYTHON_ENV="~/atlassian/src/ml-studio/ml_3.11/bin/python"

# Expand the tilde to full path
PYTHON_PATH="${PYTHON_ENV/#\~/$HOME}"

echo "Using Python environment: $PYTHON_PATH"
echo "Python version: $($PYTHON_PATH --version)"
echo "Starting Memory Trainer (Pygame Version)..."
echo ""

# Install pygame if not already installed
echo "Ensuring pygame is installed..."
"$PYTHON_PATH" -m pip install pygame > /dev/null 2>&1

# Run the trainer
exec "$PYTHON_PATH" trainer_pygame.py