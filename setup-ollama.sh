#!/bin/bash
# Script to pull Ollama model after starting the services

echo "Pulling Ollama model..."
MODEL=${OLLAMA_MODEL:-llama3.1}

# Wait for Ollama service to be ready
echo "Waiting for Ollama service to start..."
sleep 5

# Pull the model
docker exec phd-redaction-ollama ollama pull $MODEL

echo "Ollama model $MODEL has been pulled successfully!"
echo "You can now use the application with Ollama by setting LLM_PROVIDER=ollama in your .env file"
