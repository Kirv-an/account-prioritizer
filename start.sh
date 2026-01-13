#!/bin/bash

# Simple start script for the Account Prioritization Tool

echo "=================================================="
echo "Account Prioritization Tool - Starting Server"
echo "=================================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo ""
echo "Starting Flask server..."
echo "Access the application at: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python run.py