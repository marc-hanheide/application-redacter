# PhD Application Anonymisation System

AI-powered web application that anonymises PhD application documents (.docx) by removing all identifying information including names, institutions, contact details, and protected characteristics to enable fair and unbiased recruitment.

## LLM Providers

Choose between two LLM backends:
- **Anthropic Claude** (cloud-based, requires API key)
- **Ollama** (local, runs in Docker, no API key needed)

## Quick Start

**Prerequisites:** Docker and Docker Compose

### Using Anthropic Claude (Default)

1. Create `.env` file with your API key:
   ```bash
   echo "LLM_PROVIDER=anthropic" > .env
   echo "ANTHROPIC_API_KEY=your-key-here" >> .env
   ```

2. Deploy:
   ```bash
   docker compose up -d
   ```

3. Access at http://localhost:8099

### Using Ollama (Local)

1. Create `.env` file:
   ```bash
   echo "LLM_PROVIDER=ollama" > .env
   ```

2. Deploy and pull model:
   ```bash
   docker compose up -d
   chmod +x setup-ollama.sh
   ./setup-ollama.sh
   ```

3. Access at http://localhost:8099

## Configuration

Edit `.env` to configure:
- `LLM_PROVIDER`: `anthropic` or `ollama`
- `ANTHROPIC_API_KEY`: Your Anthropic API key (if using Anthropic)
- `ANTHROPIC_MODEL`: Model name (default: `claude-sonnet-4-20250514`)
- `OLLAMA_MODEL`: Model name (default: `llama3.1`)
- `OLLAMA_BASE_URL`: Ollama service URL (default: `http://ollama:11434`)

## Usage

Upload a .docx file → Process → Download anonymised document

## What Gets Redacted

- Names, institutions, employers, publication titles
- Contact details (email, phone, addresses, web links)
- Protected characteristics (age, gender, ethnicity, nationality, religion, disability, marital status)
- Geographic locations and unique identifiers

## Management

```bash
docker compose up -d          # Start
docker compose down           # Stop
docker compose logs -f        # View logs
docker compose up -d --build  # Rebuild
```

## License

MIT License
