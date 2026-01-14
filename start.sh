#!/bin/bash

# Simple start script for the Account Prioritization Tool

echo "=================================================="
echo "Account Prioritization Tool - Starting Server"
echo "=================================================="
echo ""

# Kill any existing processes on port 5001
echo "Checking for processes on port 5001..."
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "Found existing processes on port 5001. Killing them..."
    kill -9 $(lsof -ti:5001) 2>/dev/null
    echo "Processes killed."
    sleep 1
else
    echo "Port 5001 is free."
fi

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
echo "Access the application at: http://127.0.0.1:5001"
echo "Press Ctrl+C to stop the server"
echo ""

python run.py