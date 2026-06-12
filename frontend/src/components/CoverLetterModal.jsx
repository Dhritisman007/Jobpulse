import { useState } from 'react';
import { generateCoverLetter } from '../api';

export default function CoverLetterModal({ job, onClose }) {
  const [coverLetter, setCoverLetter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await generateCoverLetter(job.id);
      setCoverLetter(result.cover_letter);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(coverLetter);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const textarea = document.createElement('textarea');
      textarea.value = coverLetter;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content" id="cover-letter-modal">
        <div className="modal-header">
          <div>
            <div className="modal-title">✍️ Cover Letter Generator</div>
            <div style={{ color: 'var(--color-text-muted)', fontSize: 13, marginTop: 4 }}>
              {job.title} at {job.company}
            </div>
          </div>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {!coverLetter && !loading && (
            <div className="empty-state" style={{ padding: '32px 0' }}>
              <div className="empty-state-icon">✍️</div>
              <div className="empty-state-title">Generate a Tailored Cover Letter</div>
              <div className="empty-state-text">
                Click the button below to generate a cover letter based on your resume and this job description using Claude AI.
              </div>
              <button
                className="btn btn-primary"
                onClick={handleGenerate}
                style={{ marginTop: 16 }}
              >
                🚀 Generate Cover Letter
              </button>
            </div>
          )}

          {loading && (
            <div className="empty-state loading-pulse" style={{ padding: '32px 0' }}>
              <div className="empty-state-icon">🤖</div>
              <div className="empty-state-title">Writing your cover letter...</div>
              <div className="empty-state-text">
                Claude is crafting a personalized cover letter for this role.
              </div>
            </div>
          )}

          {error && (
            <div style={{
              padding: 16,
              background: 'var(--color-danger-dim)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-danger)',
              fontSize: 13,
              marginBottom: 16,
            }}>
              ⚠️ {error}
            </div>
          )}

          {coverLetter && (
            <>
              <textarea
                className="cover-letter-text"
                value={coverLetter}
                onChange={(e) => setCoverLetter(e.target.value)}
                rows={12}
                id="cover-letter-textarea"
              />
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginTop: 8,
                color: 'var(--color-text-muted)',
                fontSize: 12,
              }}>
                <span>✏️ Edit freely before copying</span>
                <span>{coverLetter.split(/\s+/).length} words</span>
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          {coverLetter && (
            <>
              <button className="btn btn-secondary" onClick={handleGenerate} disabled={loading}>
                🔄 Regenerate
              </button>
              <button className="btn btn-primary" onClick={handleCopy}>
                {copied ? '✅ Copied!' : '📋 Copy to Clipboard'}
              </button>
            </>
          )}
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
