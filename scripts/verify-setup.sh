#!/bin/bash
# Verification script for architecture compliance

set -e

echo "=== Voice Agent Architecture Verification ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please review and update values."
else
    echo "✅ .env file exists"
fi

# Check required files
echo ""
echo "Checking required files..."
required_files=(
    "backend/config.py"
    "backend/ari_integration.py"
    "backend/main.py"
    "backend/call_handler.py"
    "backend/websocket_stream.py"
    "backend/stt_engine.py"
    "backend/translator.py"
    "backend/tts_engine.py"
    "backend/language_detector.py"
    "backend/metrics.py"
    "docker-compose.yml"
    "requirements.txt"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING"
        exit 1
    fi
done

# Check Docker
echo ""
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker installed: $(docker --version)"
else
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose installed: $(docker-compose --version)"
else
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Validate docker-compose.yml
echo ""
echo "Validating docker-compose.yml..."
if docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors"
    docker-compose config
    exit 1
fi

# Check Python dependencies
echo ""
echo "Checking Python dependencies..."
if [ -f requirements.txt ]; then
    echo "✅ requirements.txt found with $(wc -l < requirements.txt) lines"
    
    # Check for critical dependencies
    critical_deps=("fastapi" "redis" "aiohttp" "torch" "transformers" "pydantic-settings")
    for dep in "${critical_deps[@]}"; do
        if grep -q "$dep" requirements.txt; then
            echo "  ✅ $dep"
        else
            echo "  ❌ $dep - MISSING"
        fi
    done
fi

# Check Asterisk configuration
echo ""
echo "Checking Asterisk configuration..."
if [ -f asterisk/extensions.conf ]; then
    if grep -q "Stasis(voice-agent" asterisk/extensions.conf; then
        echo "✅ Asterisk dialplan configured for Stasis"
    else
        echo "⚠️  Asterisk dialplan may need Stasis configuration"
    fi
fi

if [ -f asterisk/sip.conf ]; then
    echo "✅ SIP configuration exists"
fi

# Architecture compliance checks
echo ""
echo "=== Architecture Compliance Checks ==="

# Check for config.py
if grep -q "class Settings" backend/config.py 2>/dev/null; then
    echo "✅ Configuration management implemented"
else
    echo "❌ Configuration management missing"
fi

# Check for ARI integration
if grep -q "class ARIIntegration" backend/ari_integration.py 2>/dev/null; then
    echo "✅ ARI integration module exists"
else
    echo "❌ ARI integration module missing"
fi

# Check for proper JSON serialization
if grep -q "json.dumps" backend/call_handler.py 2>/dev/null; then
    echo "✅ Proper JSON serialization in call_handler"
else
    echo "⚠️  Check JSON serialization in call_handler"
fi

# Check for WebSocket auth
if grep -q "authorization" backend/main.py 2>/dev/null; then
    echo "✅ WebSocket authentication implemented"
else
    echo "⚠️  WebSocket authentication may be missing"
fi

# Check for Redis TTL
if grep -q "redis_ttl" backend/config.py 2>/dev/null; then
    echo "✅ Redis TTL configuration exists"
else
    echo "⚠️  Redis TTL configuration missing"
fi

echo ""
echo "=== Summary ==="
echo "Architecture verification complete!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Run: docker-compose up -d"
echo "3. Check health: curl http://localhost:8000/health"
echo "4. Monitor logs: docker-compose logs -f backend"
echo ""
echo "For detailed information, see ARCHITECTURE-FIXES.md"
