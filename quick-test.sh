#!/bin/bash
# Quick test script for Obsidian Local Sage
# Tests if configuration system is working

set -e

echo "🧙 Obsidian Local Sage - Quick Test"
echo "===================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "src/core/config.py" ]]; then
    echo "❌ Error: Must be run from obsidian-local-sage directory"
    exit 1
fi

# Check if config exists
if [[ ! -f "config/settings.yaml" ]]; then
    echo "⚠️  Config not found: config/settings.yaml"
    echo ""
    echo "Creating from template..."
    cp config/settings.example.yaml config/settings.yaml
    echo "✅ Created config/settings.yaml"
    echo ""
    echo "⚠️  Please edit config/settings.yaml and set your vault path!"
    echo "   Then run this script again."
    exit 0
fi

echo "1. Testing Python and dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi
echo "   ✅ Python 3: $(python3 --version)"

if ! python3 -c "import yaml" 2>/dev/null; then
    echo "   ⚠️  PyYAML not installed. Installing..."
    pip3 install -q pyyaml
fi
echo "   ✅ PyYAML installed"

echo ""
echo "2. Testing configuration system..."
if python3 src/core/config.py; then
    echo "   ✅ Config system working!"
else
    echo "   ❌ Config system failed"
    echo "   Please check your config/settings.yaml"
    exit 1
fi

echo ""
echo "3. Checking dependencies..."

# fzf
if command -v fzf &> /dev/null; then
    echo "   ✅ fzf: $(fzf --version)"
else
    echo "   ❌ fzf not installed (brew install fzf)"
fi

# Ollama
if command -v ollama &> /dev/null; then
    echo "   ✅ Ollama installed"
    if ollama list | grep -q "bge-m3"; then
        echo "   ✅ BGE-M3 model available"
    else
        echo "   ⚠️  BGE-M3 model not found (ollama pull bge-m3)"
    fi
else
    echo "   ❌ Ollama not installed (see INSTALL.md)"
fi

# Qdrant
if curl -s http://127.0.0.1:6333 &> /dev/null; then
    echo "   ✅ Qdrant running"
else
    echo "   ⚠️  Qdrant not running (see INSTALL.md)"
fi

echo ""
echo "4. Checking scripts..."
script_count=$(find src -name "*.py" -o -name "*.sh" | wc -l)
echo "   ✅ Found $script_count scripts"

echo ""
echo "===================================="
echo "✅ Quick test complete!"
echo ""
echo "Next steps:"
echo "1. Review config/settings.yaml"
echo "2. Run: python3 src/core/ingest-direct.py --full (to build index)"
echo "3. Configure Obsidian Shell Commands"
echo "4. Test features in Obsidian!"
echo ""
echo "See INSTALL.md for detailed instructions."
