#!/bin/bash

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

echo "Setup complete!"
echo "To run the application:"
echo "1. Start the backend server: python server.py"
echo "2. In another terminal, start the frontend: npm start"
