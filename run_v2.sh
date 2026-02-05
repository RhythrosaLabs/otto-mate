#!/bin/bash
# Otto Universal v2 - Modular Architecture Startup Script
# This starts the new modular server with service layer architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Otto Universal v2 - Modular Architecture          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file${NC}"
    else
        echo -e "${RED}❌ No .env.example found. Please create .env with required API keys.${NC}"
        exit 1
    fi
fi

# Check for required environment variables
source .env 2>/dev/null || true

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key" ]; then
    echo -e "${RED}❌ ANTHROPIC_API_KEY is not set in .env${NC}"
    echo -e "${YELLOW}   Please add your Anthropic API key to .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables loaded${NC}"

# Check Python dependencies
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
fi

# Default port
PORT=${PORT:-8001}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --port=*)
            PORT="${1#*=}"
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --prod)
            PROD_MODE=true
            shift
            ;;
        --help)
            echo "Usage: ./run_v2.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT    Port to run on (default: 8001)"
            echo "  --dev          Development mode with hot reload"
            echo "  --prod         Production mode"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo ""
echo -e "${BLUE}🚀 Starting Otto Universal v2...${NC}"
echo -e "${BLUE}   Port: $PORT${NC}"
echo -e "${BLUE}   Mode: ${DEV_MODE:+Development}${PROD_MODE:+Production}${NC}"
echo ""

# Kill any existing process on the port
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}Killing existing process on port $PORT...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
fi

# Set the port environment variable
export PORT=$PORT

# Start the server
if [ "$PROD_MODE" = true ]; then
    # Production mode - no reload, multiple workers
    echo -e "${GREEN}🏭 Starting in PRODUCTION mode${NC}"
    uvicorn backend.src.api.main_v2:app \
        --host 0.0.0.0 \
        --port $PORT \
        --workers 4 \
        --log-level info
else
    # Development mode - with reload
    echo -e "${GREEN}🔧 Starting in DEVELOPMENT mode${NC}"
    python -m backend.src.api.main_v2
fi
