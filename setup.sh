#!/bin/bash
set -e

echo "Creating virtual environment at ../env..."
python -m venv ../env

echo "Activating virtual environment..."
source ../env/bin/activate

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Installing berryaudio in editable mode..."
pip install -e .

echo "Setup complete. Run 'berryaudio' to start."