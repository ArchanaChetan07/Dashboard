#!/bin/bash
# Quick Start Script for Weelocal Dashboard

echo "=========================================="
echo "WEELOCAL DASHBOARD - QUICK START"
echo "=========================================="
echo ""

# Check Python
echo "1. Checking Python..."
python --version
if [ $? -eq 0 ]; then
    echo "   ✓ Python found"
else
    echo "   ✗ Python not found"
    exit 1
fi

# Check packages
echo ""
echo "2. Checking packages..."
python -c "import flask; print('   ✓ Flask ready')" 2>/dev/null
python -c "import openpyxl; print('   ✓ openpyxl ready')" 2>/dev/null
python -c "import xlrd; print('   ✓ xlrd ready')" 2>/dev/null

# Start server
echo ""
echo "3. Starting server..."
echo "   Running: python run_server.py"
echo ""
python run_server.py
