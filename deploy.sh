#!/bin/bash

set -e

echo "================================================"
echo "PhD Application Anonymisation System"
echo "Deployment Script"
echo "================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed."
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "================================================"
    echo "IMPORTANT: Configure your API key"
    echo "================================================"
    echo ""
    echo "Please edit .env and add your Anthropic API key:"
    echo "  nano .env"
    echo ""
    echo "Get your API key from: https://console.anthropic.com/"
    echo ""
    read -p "Press Enter after you've configured the .env file..."
fi

# Verify API key is set
source .env
if [ "$ANTHROPIC_API_KEY" = "your-api-key-here" ] || [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "Error: ANTHROPIC_API_KEY is not configured in .env file"
    echo "Please edit .env and set your API key"
    exit 1
fi

echo ""
echo "Building and starting services..."
echo ""

# Build and start services
docker-compose up -d --build

echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""
echo "The application is now running:"
echo "  • Frontend: http://localhost"
echo "  • Backend API: http://localhost/api"
echo ""
echo "Useful commands:"
echo "  • View logs:        docker-compose logs -f"
echo "  • Stop services:    docker-compose down"
echo "  • Restart services: docker-compose restart"
echo "  • Check status:     docker-compose ps"
echo ""
echo "For more information, see README.md"
echo ""
