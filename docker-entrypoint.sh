#!/bin/bash
set -e

echo "🎤 Voice Agent - Initialization"
echo "================================"

# Check environment
echo "✓ Python: $(python --version)"
echo "✓ FastAPI: $(python -c 'import fastapi; print(fastapi.__version__)')"
echo "✓ Torch: $(python -c 'import torch; print(torch.__version__)')"
echo "✓ Transformers: $(python -c 'import transformers; print(transformers.__version__)')"

# Database migrations (if needed)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Start application
exec "$@"
