# PhD Application Anonymisation System

**AgriFoRwArdS CDT - Hosted Web Application**

A complete web-based solution for anonymising PhD applications to support fair and unbiased recruitment.

## Features

- **Web-based Interface**: User-friendly React frontend
- **Comprehensive Redaction**: AI-powered removal of all identifying information
- **Preserves Formatting**: Original document structure maintained
- **Transparent Redaction**: Descriptive placeholders replace identifying information
- **Secure Processing**: Files processed on your own server
- **Easy Deployment**: One-command Docker setup

## Architecture

- **Frontend**: React.js with responsive design
- **Backend**: Python Flask API
- **AI**: Claude API for intelligent redaction
- **Document Processing**: python-docx for DOCX handling
- **Deployment**: Docker Compose orchestration
- **Web Server**: Nginx for serving and API proxy

## Prerequisites

- Docker and Docker Compose installed
- Anthropic API key (get one at https://console.anthropic.com/)
- Linux server or local machine with Docker support

## Quick Start

### 1. Extract the Application

```bash
tar -xzf phd-redaction-webapp.tar.gz
cd phd-redaction-webapp
```

### 2. Configure Environment

Create a `.env` file with your Anthropic API key:

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

Edit the file and replace `your-api-key-here` with your actual API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Deploy with Docker Compose

```bash
docker-compose up -d
```

This will:
- Build the backend and frontend Docker images
- Start the services
- Expose the application on port 80

### 4. Access the Application

Open your browser and navigate to:
- Local: http://localhost
- Server: http://your-server-ip

## Usage

1. **Upload Document**: Click to upload a .docx PhD application
2. **Process**: Click "Start Redaction Process"
3. **Review**: View the unredacted summary and applicant information
4. **Download**: Download the fully redacted document

## What Gets Redacted

**Complete anonymisation following strict equality and diversity guidelines.**

For full details, see [REDACTION_RULES.md](REDACTION_RULES.md)

### Critical Redactions:
- ✓ **ALL personal names** (applicant's name removed from EVERY instance) → `[NAME REDACTED]`
- ✓ Institution names → `[Name of University]`, `[Name of Research Institute]`
- ✓ Employer names → `[Name of Company/Organisation]`
- ✓ Publication & thesis titles → `[Title of Article]`, `[Title of Thesis]`
- ✓ Web links & profiles (LinkedIn, ResearchGate, etc.) → `[LINK REMOVED]`
- ✓ Contact details (email, phone, addresses) → `[EMAIL REDACTED]`, `[PHONE REDACTED]`

### Protected Characteristics (Equality Act Compliance):
- ✓ Age, date of birth → `[DATE REDACTED]`
- ✓ Gender, gender identity → `[REDACTED]`
- ✓ Ethnicity, race, nationality → `[REDACTED]`
- ✓ Religion, beliefs → `[REDACTED]`
- ✓ Disability, health conditions → `[REDACTED]`
- ✓ Marital status, family circumstances → `[REDACTED]`
- ✓ Sexual orientation → `[REDACTED]`

### Additional Identifying Information:
- ✓ Specific geographic locations → `[Location]`
- ✓ Unique identifiers (student IDs, grant numbers) → `[ID REDACTED]`
- ✓ Dates that could reveal age → `[Date]` or `[Year]`

**Principle**: When in doubt, REDACT IT. The system ensures complete anonymity for fair assessment.

## Management Commands

### Start the application
```bash
docker-compose up -d
```

### Stop the application
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Restart the application
```bash
docker-compose restart
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Check status
```bash
docker-compose ps
```

## File Structure

```
phd-redaction-webapp/
├── docker-compose.yml          # Docker orchestration
├── .env.example                # Environment variable template
├── .env                        # Your environment variables (create this)
├── README.md                   # This file
├── backend/
│   ├── Dockerfile              # Backend container definition
│   ├── app.py                  # Flask API application
│   └── requirements.txt        # Python dependencies
└── frontend/
    ├── Dockerfile              # Frontend container definition
    ├── nginx.conf              # Nginx configuration
    ├── package.json            # Node dependencies
    ├── public/
    │   └── index.html          # HTML template
    └── src/
        ├── App.js              # Main React component
        ├── App.css             # Application styles
        ├── index.js            # React entry point
        └── index.css           # Global styles
```

## API Endpoints

### Backend API (port 5000, proxied through nginx)

- `POST /api/process` - Upload and process a document
  - Body: multipart/form-data with 'file' field
  - Returns: summary, applicant info, download ID
  
- `GET /api/download/<download_id>` - Download redacted document
  - Returns: DOCX file

- `GET /health` - Health check endpoint

## Troubleshooting

### Port 80 already in use

If port 80 is already in use, edit `docker-compose.yml` and change:
```yaml
ports:
  - "8080:80"  # Use port 8080 instead
```

Then access at http://localhost:8080

### API Key Issues

Check the logs:
```bash
docker-compose logs backend
```

Ensure your `.env` file contains a valid API key starting with `sk-ant-`

### File Upload Issues

Check nginx configuration allows sufficient upload size (default: 20MB)

View logs:
```bash
docker-compose logs frontend
```

### Backend Processing Errors

View backend logs:
```bash
docker-compose logs backend
```

Common issues:
- Invalid API key
- API rate limits exceeded
- Malformed DOCX files

### Rebuilding After Changes

```bash
docker-compose down
docker-compose up -d --build
```

## Security Considerations

- **API Key**: Keep your `.env` file secure and never commit it to version control
- **Network**: Consider running behind a reverse proxy with HTTPS
- **Firewall**: Configure appropriate firewall rules for port 80/443
- **Data**: Processed files are stored temporarily and deleted after download
- **Access**: Consider adding authentication for production use

## Production Deployment

For production deployment:

1. **Use HTTPS**: Set up nginx with SSL certificates (Let's Encrypt)
2. **Add Authentication**: Implement user authentication
3. **Configure Firewall**: Only allow necessary ports
4. **Set up Monitoring**: Use tools like Prometheus/Grafana
5. **Regular Backups**: Backup configuration and logs
6. **Update Regularly**: Keep Docker images and dependencies updated

### Example Production Setup with SSL

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    # ... same as before
    
  frontend:
    # ... same as before
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf
```

Then run:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Support

For issues:
- Check logs with `docker-compose logs`
- Verify API key is correctly set in `.env`
- Ensure Docker and Docker Compose are up to date
- Check firewall and port settings

## Privacy and Ethics

This tool supports fair recruitment by:
- Removing unconscious bias from shortlisting
- Ensuring equality of opportunity
- Promoting diversity and inclusion
- Supporting EDI commitments in STEM fields

Gender under-representation (only 15% female undergraduates in CS/Engineering) makes anonymised recruitment essential for the AgriFoRwArdS CDT's commitment to empowering gender diversity.

## Licence

Proprietary - For use by AgriFoRwArdS CDT and authorised partners only.

## Version

Version 1.0.0 - October 2025
