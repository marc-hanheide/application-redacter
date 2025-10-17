#!/bin/bash
# Script to pull Ollama model after starting the services

set -e  # Exit on error

echo "=" 
echo "Ollama Model Setup"
echo "="

# Get model from environment or use default

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

MODEL=${OLLAMA_MODEL:-llama3.1}
echo "Model to pull: $MODEL"

# Check if Ollama container is running
echo ""
echo "Checking if Ollama service is running..."
if ! docker compose ps ollama | grep -q "Up"; then
    echo "❌ Ollama service is not running!"
    echo "Please start it first with: docker compose up -d ollama"
    exit 1
fi
echo "✓ Ollama service is running"

# Wait for Ollama service to be ready
echo ""
echo "Waiting for Ollama service to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose exec ollama ollama list &>/dev/null; then
        echo "✓ Ollama service is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "  Waiting... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ Ollama service did not become ready in time"
    exit 1
fi

# Check if model is already pulled
echo ""
echo "Checking if model is already available..."
if docker compose exec ollama ollama list | grep -q "$MODEL"; then
    echo "✓ Model $MODEL is already available"
    echo ""
    echo "You can now use the application with Ollama!"
    echo "Make sure LLM_PROVIDER=ollama in your .env file"
    exit 0
fi

# Pull the model
echo ""
echo "Pulling model $MODEL (this may take several minutes, ~5GB download)..."
echo "Please be patient..."
docker compose exec ollama ollama pull $MODEL

echo ""
echo "=" 
echo "✅ Ollama model $MODEL has been pulled successfully!"
echo "="
echo ""
echo "Next steps:"
echo "1. Ensure LLM_PROVIDER=ollama in your .env file"
echo "2. Restart backend: docker compose restart backend"
echo "3. Access the application at http://localhost:8099"
echo ""
