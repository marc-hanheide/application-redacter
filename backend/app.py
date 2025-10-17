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
import logging
import sys

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
app.logger.setLevel(logging.INFO)

logger.info("Starting PhD Application Redaction Backend")

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'docx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.info(f"Upload folder configured: {UPLOAD_FOLDER}")

# Get Anthropic API key from environment
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    logger.error("ANTHROPIC_API_KEY environment variable not set")
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")

logger.info("Anthropic API key loaded successfully")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
logger.info("Anthropic client initialized")


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


def get_claude_response(prompt, max_tokens=10000):
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
    """Extract unredacted applicant information for admin records only"""
    prompt = f"""You are analyzing a PhD application document to extract applicant information for administrative records.

IMPORTANT: This information is for ADMINISTRATIVE USE ONLY and will NOT appear in the redacted document. 
All of this information will be completely removed from the version sent for anonymous review.

Extract the following information:

1. Provide a brief summary of the application focusing on qualifications and research interests (2-3 sentences)
   - DO NOT include the applicant's name in the summary
   - Focus on their academic background and research focus

2. Extract key applicant information in JSON format with these exact fields:
   - name: full name of applicant (CRITICAL: extract ALL variations and occurrences)
   - lastQualification: their most recent degree/qualification
   - email: email address
   - phone: phone number (if available, otherwise null)
   - ethnicity: ethnicity (if mentioned, otherwise null)
   - gender: gender (if mentioned, otherwise null)
   - age: age or date of birth (if mentioned, otherwise null)
   - religion: religion (if mentioned, otherwise null)

Document text:
{document_text[:30000]}

Respond with a JSON object containing:
{{
  "summary": "...",
  "applicantInfo": {{ ... }}
}}

YOUR ENTIRE RESPONSE MUST BE VALID JSON ONLY. DO NOT INCLUDE ANY TEXT OUTSIDE THE JSON STRUCTURE."""

    return get_claude_response(prompt, max_tokens=10000)


def get_redaction_plan(document_text):
    """Get comprehensive redaction plan from Claude"""
    prompt = f"""You are redacting a PhD application document to remove ALL identifying information for completely anonymous recruitment. This is critical for fair and unbiased evaluation.

STRICT REDACTION RULES - REMOVE ALL OF THE FOLLOWING:

1. **ALL PERSONAL NAMES** - This is CRITICAL:
   - Any full name, first name, surname, middle names MUST BE REDACTED
   - ANY occurrence of the applicant's name throughout the ENTIRE document
   - Names of referees, supervisors, colleagues, collaborators
   - Authors' names in publications or references
   - Replace ALL names with [NAME REDACTED]
   - Check for names in signatures, letterheads, headers, footers

2. **Institution Names**:
   - Universities, colleges, schools attended (replace with "[NAME OF UNIVERSITY]", "[NAME OF COLLEGE]")
   - Research institutes, laboratories (replace with "[NAME OF RESEARCH INSTITUTE]")
   - Be thorough - check for institution names in addresses, email domains, affiliations

3. **Employer Names**:
   - Companies, organizations, NGOs (replace with "[NAME OF COMPANY/ORGANISATION]")
   - Government departments, agencies

4. **Publications & Research**:
   - Article titles, paper titles, thesis titles (replace with "[TITLE OF ARTICLE/PAPER/THESIS]")
   - Book titles authored by the applicant (replace with "[TITLE OF BOOK]")
   - Conference presentation titles (replace with "[TITLE OF PRESENTATION]")
   - Keep journal names and conference names (these are not identifying)

5. **Personal Contact Information**:
   - Email addresses (replace with [EMAIL REDACTED])
   - Phone numbers, mobile numbers (replace with [PHONE REDACTED])
   - Physical addresses, postal codes (replace with [ADDRESS REDACTED])
   - Social media handles, usernames (replace with [USERNAME REDACTED])
   - Web links to personal profiles, LinkedIn, ResearchGate, personal websites (replace with [LINK REMOVED])

6. **Protected Characteristics** (CRITICAL for fair recruitment):
   - remove ANY PRONOUNS that could indicate gender, replace them with the gender-neutral pronouns "they"/"their"/"them"
   - Age, date of birth, year of birth (replace with [DATE REDACTED])
   - Gender, gender identity (replace with [REDACTED])
   - Ethnicity, race, nationality, country of origin (replace with [REDACTED])
   - Religion, religious beliefs (replace with [REDACTED])
   - Disability, health conditions (replace with [REDACTED])
   - Marital status, family status, pregnancy (replace with [REDACTED])
   - Sexual orientation (replace with [REDACTED])
   - Photographs, images of the applicant (note if present)

7. **Identifying Dates**:
   - Graduation dates that could reveal age (replace with "[DATE]" or "[YEAR]")
   - Employment dates if they reveal age (replace with duration instead, e.g., "3 years")
   - Birth dates (replace with [DATE REDACTED])

8. **Geographic Identifiers**:
   - Specific cities, towns, regions where the applicant lived/studied/worked (replace with "[LOCATION REDACTED]")
   - Keep country names only if essential to understanding research context

9. **Unique Identifiers**:
   - Student ID numbers, employee numbers (replace with [ID REDACTED])
   - Grant numbers or awards that could identify the applicant (replace with "[GRANT REFERENCE REDACTED]")
   - Unique project names that could identify the applicant (replace with "[PROJECT NAME REDACTED]")

CRITICAL INSTRUCTIONS:
- Any names MUST be removed from EVERY instance it appears, also check for variations of the name and redact them, anything that looks like a name must be redacted
- Be EXHAUSTIVE - check headers, footers, signatures, contact details, CVs, personal statements
- If unsure whether something is identifying, REDACT IT - err on the side of caution
- Preserve the meaning and structure of the document, but ensure complete anonymity
- Each redaction must have the EXACT text as it appears (including capitalization, spacing)
- CRITICAL: Extract the EXACT text character-by-character from the document
- Include ALL punctuation, spaces, and formatting exactly as shown
- For names, extract each variation (e.g., "John Smith", "Smith", "J. Smith") separately
- For emails, extract the complete email address exactly as written
- For institutions, extract the complete name exactly as written

For each piece of text that needs redaction, provide:
- The exact text to find (must match exactly as it appears in the document)
- The replacement text (should be descriptive and appropriate)

Document text:
{document_text[:30000]}

Provide a comprehensive list of redactions in JSON format:
{{
  "redactions": [
    {{"find": "exact text to find", "replace": "replacement text"}},
    ...
  ]
}}

IMPORTANT: Be thorough and extract EXACT text. Even a single character difference will cause the redaction to fail.
This document MUST be completely anonymous with NO personal information that could identify the candidate.
YOUR ENTIRE RESPONSE MUST BE VALID JSON ONLY."""

    return get_claude_response(prompt, max_tokens=10000)


def apply_redactions_to_docx(input_path, output_path, redactions):
    """Apply redactions to DOCX file while preserving formatting - enhanced version"""
    doc = Document(input_path)

    # Remove all hyperlinks in the document (including display text)
    from docx.oxml.ns import qn
    link_count = 0
    def remove_hyperlinks_from_element(element):
        nonlocal link_count
        # Find all hyperlink elements
        hyperlinks = element.findall('.//w:hyperlink', namespaces=element.nsmap)
        for hyperlink in hyperlinks:
            # Get the display text (all w:t elements inside the hyperlink)
            texts = hyperlink.findall('.//w:t', namespaces=element.nsmap)
            for t in texts:
                t.text = '[LINK REMOVED]'
            # Replace the hyperlink with its children (removes the link but keeps the text)
            parent = hyperlink.getparent()
            idx = parent.index(hyperlink)
            for child in list(hyperlink):
                parent.insert(idx, child)
                idx += 1
            parent.remove(hyperlink)
            link_count += 1

    # Remove hyperlinks in main document
    remove_hyperlinks_from_element(doc._element)
    # Remove hyperlinks in headers/footers
    for section in doc.sections:
        if hasattr(section.header, '_element'):
            remove_hyperlinks_from_element(section.header._element)
        if hasattr(section.footer, '_element'):
            remove_hyperlinks_from_element(section.footer._element)
    # Remove hyperlinks in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if hasattr(cell, '_element'):
                    remove_hyperlinks_from_element(cell._element)
    logger.info(f"Removed {link_count} hyperlinks from document.")
    
    redaction_count = 0
    total_replacements = 0
    redaction_details = []  # Track each redaction with counts
    
    logger.info(f"Starting redaction process with {len(redactions)} redaction rules")
    
    def replace_in_paragraph(paragraph, find_text, replace_text):
        """Replace text in a paragraph using word boundaries for single words, verbatim for phrases"""
        replacements = 0
        
        # Determine if find_text is a single word or a multi-word phrase
        is_single_word = len(find_text.split()) == 1
        
        # Escape special regex characters in find_text
        escaped_find = re.escape(find_text)
        
        # Use word boundaries only for single words to avoid substring matches
        if is_single_word:
            pattern = r'\b' + escaped_find + r'\b'
        else:
            # For multi-word phrases, match verbatim (no word boundaries)
            pattern = escaped_find
        
        # First, try replacement in each run (fast path for most cases)
        for run in paragraph.runs:
            if run.text:
                # Count matches before replacement
                matches = re.findall(pattern, run.text, re.IGNORECASE)
                if matches:
                    # Replace using regex
                    new_text = re.sub(pattern, replace_text, run.text, flags=re.IGNORECASE)
                    run.text = new_text
                    replacements += len(matches)
        
        # If text wasn't found in any run but might exist in paragraph.text,
        # it's split across runs - use paragraph-level replacement
        full_text = paragraph.text
        if replacements == 0 and re.search(pattern, full_text, re.IGNORECASE):
            # Count occurrences
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            count = len(matches)
            
            # Replace in full text using regex
            new_text = re.sub(pattern, replace_text, full_text, flags=re.IGNORECASE)
            
            # Clear existing runs and create new one with replaced text
            # This preserves the paragraph but loses run-level formatting
            for run in paragraph.runs:
                run.text = ''
            
            if paragraph.runs:
                paragraph.runs[0].text = new_text
            else:
                paragraph.add_run(new_text)
            
            replacements = count
            logger.info(f"Applied paragraph-level replacement for split text: '{find_text[:50]}' ({count} times)")
        
        return replacements
    
    # Apply redactions to main document paragraphs
    for paragraph in doc.paragraphs:
        for redaction in redactions:
            find_text = redaction['find']
            replace_text = redaction['replace']
            
            count = replace_in_paragraph(paragraph, find_text, replace_text)
            if count > 0:
                total_replacements += count
                # Track this redaction
                existing = next((r for r in redaction_details if r['find'] == find_text), None)
                if existing:
                    existing['count'] += count
                else:
                    redaction_details.append({
                        'find': find_text,
                        'replace': replace_text,
                        'count': count
                    })
    
    # Apply redactions to headers
    for section in doc.sections:
        # Header
        header = section.header
        for paragraph in header.paragraphs:
            for redaction in redactions:
                find_text = redaction['find']
                replace_text = redaction['replace']
                
                count = replace_in_paragraph(paragraph, find_text, replace_text)
                if count > 0:
                    total_replacements += count
                    existing = next((r for r in redaction_details if r['find'] == find_text), None)
                    if existing:
                        existing['count'] += count
                    else:
                        redaction_details.append({
                            'find': find_text,
                            'replace': replace_text,
                            'count': count
                        })
        
        # Footer
        footer = section.footer
        for paragraph in footer.paragraphs:
            for redaction in redactions:
                find_text = redaction['find']
                replace_text = redaction['replace']
                
                count = replace_in_paragraph(paragraph, find_text, replace_text)
                if count > 0:
                    total_replacements += count
                    existing = next((r for r in redaction_details if r['find'] == find_text), None)
                    if existing:
                        existing['count'] += count
                    else:
                        redaction_details.append({
                            'find': find_text,
                            'replace': replace_text,
                            'count': count
                        })
    
    # Apply redactions to tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for redaction in redactions:
                        find_text = redaction['find']
                        replace_text = redaction['replace']
                        
                        count = replace_in_paragraph(paragraph, find_text, replace_text)
                        if count > 0:
                            total_replacements += count
                            existing = next((r for r in redaction_details if r['find'] == find_text), None)
                            if existing:
                                existing['count'] += count
                            else:
                                redaction_details.append({
                                    'find': find_text,
                                    'replace': replace_text,
                                    'count': count
                                })
    
    doc.save(output_path)
    logger.info(f"Redaction complete: {len(redaction_details)} unique patterns processed, {total_replacements} total replacements made")
    
    return total_replacements, redaction_details


def verify_redactions(file_path, redactions):
    """Verify that redactions were applied successfully by checking for remaining sensitive text"""
    doc = Document(file_path)
    full_text = []
    
    # Extract all text from the redacted document
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            full_text.append(paragraph.text)
        for paragraph in section.footer.paragraphs:
            full_text.append(paragraph.text)
    
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    full_text.append(paragraph.text)
    
    document_text = '\n'.join(full_text)
    
    # Check for any remaining sensitive text
    missed_redactions = []
    for redaction in redactions:
        find_text = redaction['find']
        
        # Determine if find_text is a single word or a multi-word phrase
        is_single_word = len(find_text.split()) == 1
        
        # Escape special regex characters
        escaped_find = re.escape(find_text)
        
        # Use word boundaries only for single words
        if is_single_word:
            pattern = r'\b' + escaped_find + r'\b'
        else:
            # For multi-word phrases, match verbatim
            pattern = escaped_find
        
        # Search for the pattern (case-insensitive)
        matches = re.findall(pattern, document_text, re.IGNORECASE)
        if matches:
            count = len(matches)
            missed_redactions.append({
                'text': find_text,
                'count': count,
                'replacement': redaction['replace']
            })
            logger.warning(f"VERIFICATION FAILED: '{find_text}' still found {count} time(s) in redacted document")
    
    if missed_redactions:
        logger.error(f"Redaction verification failed! {len(missed_redactions)} patterns still present in document")
        return False, missed_redactions
    else:
        logger.info("Redaction verification passed: no sensitive text found in redacted document")
        return True, []


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
        app.logger.info(f"Applying {len(redactions)} redaction rules...")
        for i, redaction in enumerate(redactions[:5], 1):  # Log first 5 redactions
            app.logger.info(f"  Redaction {i}: '{redaction['find'][:50]}...' -> '{redaction['replace']}'")
        if len(redactions) > 5:
            app.logger.info(f"  ... and {len(redactions) - 5} more redactions")
        
        output_filename = f"redacted_{filename}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        redaction_count, redaction_details = apply_redactions_to_docx(input_path, output_path, redactions)
        
        # Step 5: Verify redactions
        app.logger.info("Verifying redactions...")
        verification_passed, missed = verify_redactions(output_path, redactions)
        
        # Step 6: Second pass for missed redactions
        if not verification_passed and missed:
            app.logger.warning(f"First pass missed {len(missed)} patterns. Attempting second pass with enhanced matching...")
            
            # Create enhanced redactions for second pass
            # Include case-insensitive variations and common patterns
            enhanced_redactions = []
            for m in missed:
                original_text = m['text']
                replacement = m['replacement']
                
                # Add original
                enhanced_redactions.append({'find': original_text, 'replace': replacement})
                
                # Try with different whitespace (common in forms/tables)
                normalized = ' '.join(original_text.split())
                if normalized != original_text:
                    enhanced_redactions.append({'find': normalized, 'replace': replacement})
                
                # For email addresses, try without spaces
                if '@' in original_text:
                    no_space = original_text.replace(' ', '')
                    if no_space != original_text:
                        enhanced_redactions.append({'find': no_space, 'replace': replacement})
                
                app.logger.info(f"Second pass will try variations for: '{original_text[:50]}'")
            
            # Apply second pass
            temp_output = output_path + ".temp"
            second_pass_count, second_pass_details = apply_redactions_to_docx(output_path, temp_output, enhanced_redactions)
            
            # Merge second pass details into main details
            for detail in second_pass_details:
                existing = next((r for r in redaction_details if r['find'] == detail['find']), None)
                if existing:
                    existing['count'] += detail['count']
                else:
                    redaction_details.append(detail)
            
            redaction_count += second_pass_count
            
            # Replace output with second pass result
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_output, output_path)
            
            app.logger.info(f"Second pass applied {second_pass_count} additional replacements")
            
            # Verify again
            verification_passed, missed = verify_redactions(output_path, redactions)
        
        if not verification_passed:
            app.logger.error(f"Verification found {len(missed)} patterns still present:")
            for miss in missed[:5]:  # Log first 5 missed
                app.logger.error(f"  Still found: '{miss['text'][:50]}...' ({miss['count']} occurrences)")
            
            # Log warning but continue - document will be available but flagged
            app.logger.warning("Document processed but redaction may be incomplete. Manual review recommended.")
        else:
            app.logger.info("All redactions verified successfully!")
        
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
        # Store original filename for download
        session_metadata = os.path.join(UPLOAD_FOLDER, f"{session_id}.meta")
        
        with open(session_file, 'wb') as f:
            f.write(redacted_file_data)
        
        # Save original filename metadata
        import json
        with open(session_metadata, 'w') as f:
            json.dump({'original_filename': filename}, f)
        
        return jsonify({
            'summary': applicant_data.get('summary', ''),
            'applicantInfo': applicant_data.get('applicantInfo', {}),
            'redactionCount': redaction_count,
            'redactionDetails': sorted(redaction_details, key=lambda x: x['count'], reverse=True),  # Sort by count, most first
            'downloadId': session_id,
            'fileName': output_filename,
            'redactionVerified': verification_passed,
            'missedRedactions': missed if not verification_passed else []
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error processing document: {str(e)}")
        return jsonify({'error': f'Error processing document: {str(e)}'}), 500


@app.route('/api/download/<download_id>', methods=['GET'])
def download_document(download_id):
    """Download redacted document"""
    try:
        session_file = os.path.join(UPLOAD_FOLDER, f"{download_id}.docx")
        session_metadata = os.path.join(UPLOAD_FOLDER, f"{download_id}.meta")
        
        if not os.path.exists(session_file):
            return jsonify({'error': 'File not found or expired'}), 404
        
        # Load original filename from metadata
        original_filename = "application.docx"  # default fallback
        if os.path.exists(session_metadata):
            try:
                import json
                with open(session_metadata, 'r') as f:
                    metadata = json.load(f)
                    original_filename = metadata.get('original_filename', 'application.docx')
            except:
                pass
        
        # Create redacted filename: basename_redacted.docx
        base_name = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
        redacted_filename = f"{base_name}_redacted.docx"
        
        # Send file and then delete it
        response = send_file(
            session_file,
            as_attachment=True,
            download_name=redacted_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        # Schedule file deletion after sending
        @response.call_on_close
        def cleanup():
            try:
                os.remove(session_file)
                if os.path.exists(session_metadata):
                    os.remove(session_metadata)
            except:
                pass
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error downloading document: {str(e)}")
        return jsonify({'error': f'Error downloading document: {str(e)}'}), 500


if __name__ == '__main__':
    logger.info("Starting Flask server on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
