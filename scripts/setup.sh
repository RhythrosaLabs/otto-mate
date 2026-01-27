#!/bin/bash
# Setup script for Otto Universal

echo "🚀 Setting up Otto Universal..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ Python 3.11+ required. You have Python $python_version"
    exit 1
fi

echo "✅ Python version OK: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/chroma data/uploads data/screenshots logs

# Copy env file if doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp config/.env.example .env
    echo "⚠️  Please edit .env with your API keys!"
else
    echo "✅ .env file already exists"
fi

# Create init files for tools directories
echo "🔧 Setting up tool directories..."
mkdir -p src/tools/business src/tools/computer src/tools/communication
touch src/tools/__init__.py
touch src/tools/business/__init__.py
touch src/tools/computer/__init__.py
touch src/tools/communication/__init__.py
touch src/utils/__init__.py
touch src/api/__init__.py

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Run Otto: python -m src.api.main"
echo ""
echo "Or use Docker: docker-compose up"
echo ""
