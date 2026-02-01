#!/bin/bash
# Production build script for DSMS

echo "🔧 Installing Python dependencies..."
pip install -r src/dsms/requirements.txt

echo "📦 Installing Node.js dependencies..."
npm install

echo "🏗️ Building frontend..."
npm run build

echo "✅ Build complete!"
