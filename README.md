# PhD Application Anonymisation System

AI-powered web application that anonymises PhD application documents (.docx) by removing all identifying information including names, institutions, contact details, and protected characteristics to enable fair and unbiased recruitment.

## Quick Start

**Prerequisites:** Docker, Docker Compose, and an Anthropic API key

1. Create `.env` file with your API key:
   ```bash
   echo "ANTHROPIC_API_KEY=your-key-here" > .env
   ```

2. Deploy:
   ```bash
   docker compose up -d
   ```

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
