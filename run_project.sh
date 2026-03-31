#!/bin/bash
set -e

# Create virtual environment if it doesn't exist
if [ ! -d "udw_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv udw_env
fi

# Activate virtual environment
source udw_env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r udw2026_paper/requirements.txt

# Download data
echo "Downloading UD treebanks..."
python3 udw2026_paper/download_data.py

# Run analysis
echo "Running analysis..."
python3 udw2026_paper/analyze_ud.py

# Generate plots
echo "Generating plots..."
python3 udw2026_paper/plot_results.py

echo "Done! Results are in udw2026_paper/results.csv and udw2026_paper/plots/"
