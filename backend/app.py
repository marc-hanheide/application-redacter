from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import anthropic
import tempfile
import zipfile
import shutil
from docx import Document
import re
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'docx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Get Anthropic API key from environment
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    doc = Document(file_path)
    full_text = []
    
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                full_text.append(cell.text)
    
    return '\n'.join(full_text)


def get_claude_response(prompt, max_tokens=4000):
    """Get response from Claude API"""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text.strip()
        # Clean up JSON formatting
        response_text = response_text.replace('```json\n', '').replace('```\n', '').replace('```', '').strip()
        
        import json
        return json.loads(response_text)
    except Exception as e:
        app.logger.error(f"Claude API error: {str(e)}")
        raise


def extract_applicant_info(document_text):
    """Extract unredacted applicant information"""
    prompt = f"""You are analyzing a PhD application document. Extract the following information:

1. Provide a brief summary of the application (2-3 sentences)
2. Extract key applicant information in JSON format with these exact fields:
   - name: full name of applicant
   - lastQualification: their most recent degree/qualification
   - email: email address
   - phone: phone number (if available, otherwise null)
   - ethnicity: ethnicity (if mentioned, otherwise null)
   - gender: gender (if mentioned, otherwise null)
   - age: age or date of birth (if mentioned, otherwise null)
   - religion: religion (if mentioned, otherwise null)

Document text:
{document_text[:10000]}

Respond with a JSON object containing:
{{
  "summary": "...",
  "applicantInfo": {{ ... }}
}}

YOUR ENTIRE RESPONSE MUST BE VALID JSON ONLY. DO NOT INCLUDE ANY TEXT OUTSIDE THE JSON STRUCTURE."""

    return get_claude_response(prompt, max_tokens=2000)


def get_redaction_plan(document_text):
    """Get comprehensive redaction plan from Claude"""
    prompt = f"""You are redacting a PhD application document to remove ALL identifying information for anonymous recruitment.

REDACTION RULES:
1. Remove all personal names (replace with [NAME REDACTED])
2. Remove specific institution names (replace with descriptive text like "[Name of University]", "[Name of Research Institute]")
3. Remove specific employer names (replace with "[Name of Company/Organisation]")
4. Remove article titles (replace with "[Title of Article]")
5. Remove web links to personal profiles (replace with [LINK REMOVED])
6. Remove any identifying characteristics: age, gender, ethnicity, nationality, religion, disability, marital status, etc.
7. Remove addresses, email addresses, phone numbers
8. Remove specific dates that could identify age (replace with "[Date]")
9. Keep journal names and general descriptions of work

For each piece of text that needs redaction, provide:
- The exact text to find (must match exactly as it appears in the document)
- The replacement text (should be descriptive, e.g., "University of Oxford" → "[Name of University]")

Document text:
{document_text[:10000]}

Provide a comprehensive list of redactions in JSON format:
{{
  "redactions": [
    {{"find": "exact text to find", "replace": "replacement text"}},
    ...
  ]
}}

Be thorough - identify ALL instances that need redaction according to the rules above.
YOUR ENTIRE RESPONSE MUST BE VALID JSON ONLY."""

    return get_claude_response(prompt, max_tokens=4000)


def apply_redactions_to_docx(input_path, output_path, redactions):
    """Apply redactions to DOCX file while preserving formatting"""
    doc = Document(input_path)
    
    redaction_count = 0
    
    # Apply redactions to paragraphs
    for paragraph in doc.paragraphs:
        for redaction in redactions:
            find_text = redaction['find']
            replace_text = redaction['replace']
            
            if find_text in paragraph.text:
                # Replace text while preserving formatting
                for run in paragraph.runs:
                    if find_text in run.text:
                        run.text = run.text.replace(find_text, replace_text)
                        redaction_count += 1
    
    # Apply redactions to tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for redaction in redactions:
                        find_text = redaction['find']
                        replace_text = redaction['replace']
                        
                        if find_text in paragraph.text:
                            for run in paragraph.runs:
                                if find_text in run.text:
                                    run.text = run.text.replace(find_text, replace_text)
                                    redaction_count += 1
    
    doc.save(output_path)
    app.logger.info(f"Applied {redaction_count} redactions")
    
    return redaction_count


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/process', methods=['POST'])
def process_document():
    """Process uploaded DOCX file and return redacted version"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .docx files are allowed'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        app.logger.info(f"Processing file: {filename}")
        
        # Step 1: Extract text
        document_text = extract_text_from_docx(input_path)
        app.logger.info(f"Extracted {len(document_text)} characters")
        
        # Step 2: Extract applicant information
        app.logger.info("Extracting applicant information...")
        applicant_data = extract_applicant_info(document_text)
        
        # Step 3: Get redaction plan
        app.logger.info("Generating redaction plan...")
        redaction_data = get_redaction_plan(document_text)
        redactions = redaction_data.get('redactions', [])
        
        # Step 4: Apply redactions
        app.logger.info(f"Applying {len(redactions)} redactions...")
        output_filename = f"redacted_{filename}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        redaction_count = apply_redactions_to_docx(input_path, output_path, redactions)
        
        # Read the redacted file into memory
        with open(output_path, 'rb') as f:
            redacted_file_data = f.read()
        
        # Clean up files
        os.remove(input_path)
        os.remove(output_path)
        
        # Store redacted file temporarily with a session key
        import uuid
        session_id = str(uuid.uuid4())
        session_file = os.path.join(UPLOAD_FOLDER, f"{session_id}.docx")
        with open(session_file, 'wb') as f:
            f.write(redacted_file_data)
        
        return jsonify({
            'summary': applicant_data.get('summary', ''),
            'applicantInfo': applicant_data.get('applicantInfo', {}),
            'redactionCount': redaction_count,
            'downloadId': session_id,
            'fileName': output_filename
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error processing document: {str(e)}")
        return jsonify({'error': f'Error processing document: {str(e)}'}), 500


@app.route('/api/download/<download_id>', methods=['GET'])
def download_document(download_id):
    """Download redacted document"""
    try:
        session_file = os.path.join(UPLOAD_FOLDER, f"{download_id}.docx")
        
        if not os.path.exists(session_file):
            return jsonify({'error': 'File not found or expired'}), 404
        
        # Send file and then delete it
        response = send_file(
            session_file,
            as_attachment=True,
            download_name=f"redacted_application.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        # Schedule file deletion after sending
        @response.call_on_close
        def cleanup():
            try:
                os.remove(session_file)
            except:
                pass
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error downloading document: {str(e)}")
        return jsonify({'error': f'Error downloading document: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
