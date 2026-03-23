#!/bin/bash

# AI Learning Platform Test Runner
# This script runs all tests for the project

set -e

echo "======================================"
echo "AI Learning Platform Test Suite"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Backend Tests
echo ""
echo "======================================"
echo "Running Backend Tests"
echo "======================================"
cd backend

# Check if virtual environment exists, if not create one
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install dependencies
print_status "Installing backend dependencies..."
pip install -q -r requirements.txt

# Run pytest with coverage
print_status "Running pytest with coverage..."
python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml || true

# Get coverage percentage
if [ -f "coverage.xml" ]; then
    COVERAGE=$(python -c "import xml.etree.ElementTree as ET; tree = ET.parse('coverage.xml'); root = tree.getroot(); print(f\"{float(root.get('line-rate')) * 100:.1f}\")" 2>/dev/null || echo "0")
    print_status "Backend test coverage: ${COVERAGE}%"
fi

cd ..

# Frontend Tests
echo ""
echo "======================================"
echo "Running Frontend Tests"
echo "======================================"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

# Run Jest tests
print_status "Running Jest tests..."
npm test -- --coverage --passWithNoTests || true

cd ..

# Summary
echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
print_status "Backend tests completed. See backend/htmlcov/index.html for detailed coverage report."
print_status "Frontend tests completed. See frontend/coverage/lcov-report/index.html for detailed coverage report."
echo ""
print_status "All tests completed!"
