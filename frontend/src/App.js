import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Use relative URL to proxy through Nginx - no need to specify backend port
  const API_URL = '';

  const handleFileUpload = (event) => {
    const uploadedFile = event.target.files[0];
    if (uploadedFile && uploadedFile.name.endsWith('.docx')) {
      setFile(uploadedFile);
      setResults(null);
      setError(null);
    } else {
      setError('Please upload a .docx file');
    }
  };

  const processDocument = async () => {
    if (!file) return;

    setProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/api/process`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to process document');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error('Processing error:', err);
      setError(err.message || 'Error processing document');
    } finally {
      setProcessing(false);
    }
  };

  const downloadRedactedDocument = () => {
    if (!results || !results.downloadId) return;
    
    window.location.href = `${API_URL}/api/download/${results.downloadId}`;
  };

  return (
    <div className="app">
      <div className="container">
        <div className="card">
          <h1 className="title">
            PhD Application Anonymisation System
          </h1>
          <p className="subtitle">
            AgriFoRwArdS CDT - Ensuring Fair and Anonymous Recruitment
          </p>

          <div className="info-banner">
            <p>
              <strong>Anonymised Recruitment Process:</strong> This tool removes all identifying information 
              from PhD applications to mitigate unconscious bias and ensure equality of opportunity. 
              All names, institutions, employers, article titles, and personal characteristics will be redacted.
            </p>
          </div>

          <div className="upload-section">
            <label className="upload-label">
              Upload PhD Application Document (.docx)
            </label>
            <input
              type="file"
              accept=".docx"
              onChange={handleFileUpload}
              className="file-input"
            />
            {file && (
              <p className="file-selected">
                Selected: {file.name}
              </p>
            )}
          </div>

          <button
            onClick={processDocument}
            disabled={!file || processing}
            className="process-button"
          >
            {processing ? 'Processing Document...' : 'Start Redaction Process'}
          </button>

          {error && (
            <div className="error-banner">
              <p>{error}</p>
            </div>
          )}

          {results && (
            <div className="results-section">
              <div className="result-card">
                <h2 className="section-title">Unredacted Summary</h2>
                <p className="summary-text">{results.summary}</p>
              </div>

              <div className="result-card">
                <h2 className="section-title">Unredacted Applicant Information</h2>
                <div className="table-container">
                  <table className="info-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Last Qualification</th>
                        <th>Email Address</th>
                        <th>Phone</th>
                        <th>Ethnicity</th>
                        <th>Gender</th>
                        <th>Age</th>
                        <th>Religion</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>{results.applicantInfo.name || '-'}</td>
                        <td>{results.applicantInfo.lastQualification || '-'}</td>
                        <td>{results.applicantInfo.email || '-'}</td>
                        <td>{results.applicantInfo.phone || '-'}</td>
                        <td>{results.applicantInfo.ethnicity || '-'}</td>
                        <td>{results.applicantInfo.gender || '-'}</td>
                        <td>{results.applicantInfo.age || '-'}</td>
                        <td>{results.applicantInfo.religion || '-'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {!results.redactionVerified && (
                <div className="result-card warning">
                  <h2 className="section-title">Manual Redaction Required</h2>
                  <p className="warning-text">
                    <strong>Warning:</strong> Some identifying information could not be automatically redacted.<br />
                    Please review the document and manually remove the following items before sharing:
                  </p>
                  <ul className="missed-list">
                    {results.missedRedactions && results.missedRedactions.length > 0 ? (
                      results.missedRedactions.map((miss, idx) => (
                        <li key={idx}>
                          <strong>{miss.text}</strong>
                          {miss.count ? ` (${miss.count} occurrence${miss.count > 1 ? 's' : ''})` : ''}
                          {miss.replacement ? ` → should be replaced with: ${miss.replacement}` : ''}
                        </li>
                      ))
                    ) : (
                      <li>No details available.</li>
                    )}
                  </ul>
                </div>
              )}

              <div className="result-card success">
                <h2 className="section-title">Redacted Document Ready</h2>
                <p className="success-text">
                  {results.redactionVerified
                    ? 'All identifying information has been removed. The document is now ready for anonymous review.'
                    : 'Some identifying information may remain. Please review the list above and manually redact as needed.'}
                </p>
                <p className="meta-text">
                  {results.redactionCount} redactions applied
                </p>
                <button
                  onClick={downloadRedactedDocument}
                  className="download-button"
                >
                  Download Redacted Document
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="footer">
          <p>
            This anonymisation process supports the AgriFoRwArdS CDT commitment to 
            Equality, Diversity and Inclusion in recruitment.
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
