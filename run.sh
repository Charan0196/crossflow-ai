#!/bin/bash

# CrossFlow AI Trading Platform - Development Runner
echo "🚀 Starting CrossFlow AI Trading Platform..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
echo_info "Checking prerequisites..."

if ! command_exists python3; then
    echo_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

if ! command_exists node; then
    echo_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

if ! command_exists npm; then
    echo_error "npm is not installed. Please install npm."
    exit 1
fi

echo_success "All prerequisites are installed"

# Check if PostgreSQL is running
if ! command_exists psql; then
    echo_warning "PostgreSQL client not found. Make sure PostgreSQL is installed and running."
else
    echo_success "PostgreSQL client found"
fi

# Setup backend
echo_info "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo_info "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo_info "Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo_warning ".env file not found. Copying from .env.example..."
    cp .env.example .env
    echo_warning "Please edit backend/.env with your API keys and database credentials"
fi

# Start backend server in background
echo_info "Starting backend server..."
if port_in_use 8000; then
    echo_warning "Port 8000 is already in use. Stopping existing process..."
    pkill -f "uvicorn.*8000" || true
    sleep 2
fi

python -m src.main &
BACKEND_PID=$!
echo_success "Backend server started (PID: $BACKEND_PID)"

# Setup frontend
echo_info "Setting up frontend..."
cd ../frontend

# Install Node.js dependencies
if [ ! -d "node_modules" ]; then
    echo_info "Installing Node.js dependencies..."
    npm install
else
    echo_info "Node.js dependencies already installed"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo_warning ".env file not found. Copying from .env.example..."
    cp .env.example .env
    echo_warning "Please edit frontend/.env with your API keys"
fi

# Start frontend server in background
echo_info "Starting frontend server..."
if port_in_use 5173; then
    echo_warning "Port 5173 is already in use. Stopping existing process..."
    pkill -f "vite.*5173" || true
    sleep 2
fi

npm run dev &
FRONTEND_PID=$!
echo_success "Frontend server started (PID: $FRONTEND_PID)"

# Wait for servers to start
echo_info "Waiting for servers to start..."
sleep 5

# Check if servers are running
if port_in_use 8000; then
    echo_success "Backend server is running on http://localhost:8000"
    echo_info "API Documentation: http://localhost:8000/docs"
else
    echo_error "Backend server failed to start"
fi

if port_in_use 5173; then
    echo_success "Frontend server is running on http://localhost:5173"
else
    echo_error "Frontend server failed to start"
fi

echo ""
echo_success "🎉 CrossFlow AI Trading Platform is now running!"
echo_info "Frontend: http://localhost:5173"
echo_info "Backend API: http://localhost:8000"
echo_info "API Docs: http://localhost:8000/docs"
echo ""
echo_info "Press Ctrl+C to stop all servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo_info "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo_success "Servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Wait for user to stop
wait