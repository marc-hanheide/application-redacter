# Quick Setup Guide

## Choose Your LLM Provider

### Option A: Anthropic Claude (Cloud-based)
✅ Best for: Production use, high quality results, fast processing  
⚠️ Requires: API key, internet connection, costs per API call

**Setup:**
```bash
# 1. Create .env file
cat > .env << EOF
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-actual-api-key-here
EOF

# 2. Start services
docker compose up -d

# 3. Access application
# Open http://localhost:8099
```

### Option B: Ollama (Local)
✅ Best for: Privacy, development, no API costs  
⚠️ Requires: More disk space, slower processing (depending on hardware)

**Setup:**
```bash
# 1. Create .env file
cat > .env << EOF
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
EOF

# 2. Start services
docker compose up -d

# 3. Pull the model (one-time, ~4GB download)
./setup-ollama.sh

# 4. Access application
# Open http://localhost:8099
```

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | Which provider to use: `anthropic` or `ollama` | `anthropic` | Yes |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | - | If using Anthropic |
| `ANTHROPIC_MODEL` | Claude model to use | `claude-sonnet-4-20250514` | No |
| `OLLAMA_BASE_URL` | Ollama service URL | `http://ollama:11434` | No |
| `OLLAMA_MODEL` | Ollama model to use | `llama3.1` | No |

## Switching Providers

To switch from one provider to another:

```bash
# 1. Edit .env and change LLM_PROVIDER
nano .env

# 2. If switching to Ollama and haven't pulled model yet:
./setup-ollama.sh

# 3. Restart backend
docker compose restart backend

# 4. Check logs
docker compose logs -f backend
```

## Troubleshooting

### Anthropic Issues
```bash
# Check if API key is set
docker compose exec backend env | grep ANTHROPIC

# View backend logs
docker compose logs backend

# Common error: Invalid API key
# Solution: Verify your API key in .env starts with sk-ant-
```

### Ollama Issues
```bash
# Check if Ollama is running
docker compose ps ollama

# Check if model is pulled
docker exec phd-redaction-ollama ollama list

# Pull model manually
docker exec phd-redaction-ollama ollama pull llama3.1

# View Ollama logs
docker compose logs ollama
```

## Available Ollama Models

Popular models you can use:
- `llama3.1` (default, ~4GB) - Good balance of speed and quality
- `llama3.1:70b` (~40GB) - Higher quality, slower
- `mistral` (~4GB) - Fast, efficient
- `mixtral` (~26GB) - High quality
- `qwen2.5` (~4GB) - Good for structured outputs

To use a different model:
```bash
# Edit .env
echo "OLLAMA_MODEL=mistral" >> .env

# Pull the new model
docker exec phd-redaction-ollama ollama pull mistral

# Restart backend
docker compose restart backend
```

## Testing

Test your setup:
1. Open http://localhost:8099
2. Upload a sample .docx file
3. Click "Start Redaction Process"
4. Check backend logs for any errors: `docker compose logs -f backend`
5. Download the redacted document

## Performance Tips

**For Anthropic:**
- Claude Sonnet 4 is fast and high-quality (recommended)
- Monitor API costs in Anthropic console

**For Ollama:**
- Larger models = better quality but slower
- Ensure adequate RAM (8GB+ recommended)
- Use GPU if available for faster inference
- First request may be slow (model loading)

## Support

Check logs for errors:
```bash
docker compose logs -f
```

Specific service logs:
```bash
docker compose logs backend    # Backend API logs
docker compose logs ollama      # Ollama service logs
docker compose logs frontend    # Nginx logs
```
