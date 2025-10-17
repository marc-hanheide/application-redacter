# PhD Application Anonymisation System - Deployment Guide

## Quick Deployment (5 minutes)

### Step 1: Download and Extract
```bash
# Download the tar file to your server
wget http://your-server/phd-redaction-webapp.tar.gz

# Extract
tar -xzf phd-redaction-webapp.tar.gz
cd phd-redaction-webapp
```

### Step 2: Configure API Key
```bash
# Copy the environment template
cp .env.example .env

# Edit and add your Anthropic API key
nano .env
```

In the .env file, replace:
```
ANTHROPIC_API_KEY=your-api-key-here
```

With your actual key from https://console.anthropic.com/:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx
```

### Step 3: Deploy
```bash
# Use the automated deployment script
./deploy.sh

# OR manually with docker-compose
docker-compose up -d
```

### Step 4: Access
Open your browser and go to:
- **Local machine**: http://localhost
- **Remote server**: http://your-server-ip

## Application Structure

```
Frontend (React + Nginx) :80 ─────┐
                                  │
                                  ├──> User Interface
                                  │
                                  ├──> Nginx Proxy (/api/*) ──> Backend (Flask) :5000 (internal)
                                  │                                │
                                  │                                ├──> Claude API (redaction)
                                  │                                └──> python-docx (document processing)
                                  └──────────────────────────────────
```

**Note**: The backend runs on port 5000 internally within the Docker network, but is only accessible through the Nginx proxy. All external traffic uses port 80 (or 8099 as configured).

## What It Does

1. **Upload**: User uploads .docx PhD application
2. **Extract**: Backend extracts text and structure
3. **Analyse**: Claude AI identifies applicant info and redaction targets
4. **Redact**: Document is redacted while preserving formatting
5. **Download**: User downloads anonymised .docx file

## Key Features

✅ Complete web-based solution  
✅ No command-line required for end users  
✅ Preserves Word document formatting  
✅ AI-powered intelligent redaction  
✅ Separate unredacted summary for admin  
✅ Secure server-side processing  
✅ One-command deployment  

## Management Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# Restart services
docker-compose restart

# Rebuild after changes
docker-compose up -d --build

# Check service status
docker-compose ps
```

## Troubleshooting

### Port 80 Already in Use
Edit `docker-compose.yml`:
```yaml
services:
  frontend:
    ports:
      - "8080:80"  # Change to 8080
```
Then access at http://localhost:8080

### API Key Error
Check your .env file:
```bash
cat .env
```
Ensure it starts with `sk-ant-`

View backend logs:
```bash
docker-compose logs backend | grep -i "api key"
```

### Services Not Starting
Check status:
```bash
docker-compose ps
```

View all logs:
```bash
docker-compose logs
```

### File Upload Fails
Check maximum file size in `frontend/nginx.conf`:
```nginx
client_max_body_size 20M;
```

Increase if needed, then rebuild:
```bash
docker-compose up -d --build frontend
```

## System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **RAM**: Minimum 2GB (4GB recommended)
- **Disk**: 2GB free space
- **Network**: Internet access for Claude API

## Security Notes

⚠️ **Never commit .env file to version control**  
⚠️ **Use HTTPS in production (configure SSL with Let's Encrypt)**  
⚠️ **Consider adding authentication for production use**  
⚠️ **Regularly update Docker images**  
⚠️ **Keep API key secure**  

## Production Recommendations

1. **SSL/TLS**: Configure HTTPS with Let's Encrypt
2. **Firewall**: Only expose necessary ports
3. **Authentication**: Add user login system
4. **Monitoring**: Set up logging and alerting
5. **Backups**: Regular configuration backups
6. **Rate Limiting**: Prevent API abuse
7. **Updates**: Keep dependencies updated

## API Endpoints

### POST /api/process
Upload and process a document
- **Content-Type**: multipart/form-data
- **Body**: file (DOCX document)
- **Response**: JSON with summary, applicant info, and download ID

### GET /api/download/:id
Download redacted document
- **Response**: DOCX file

### GET /health
Health check
- **Response**: {"status": "healthy"}

## File Limits

- **Maximum file size**: 16MB (configurable)
- **Allowed formats**: .docx only
- **Processing timeout**: 5 minutes

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify API key configuration
3. Ensure Docker services are running
4. Check firewall settings
5. Review README.md for detailed docs

## Version
1.0.0 - October 2025

Supporting fair and unbiased recruitment in academic institutions.
