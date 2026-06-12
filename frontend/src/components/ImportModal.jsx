import { useState } from 'react';
import { importJob } from '../api';

export default function ImportModal({ onClose, onImported }) {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [description, setDescription] = useState('');
  const [source, setSource] = useState('linkedin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    try {
      await importJob({ url, title, company, description, source });
      onImported?.();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content" id="import-modal">
        <div className="modal-header">
          <div className="modal-title">➕ Import Job Manually</div>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>

        <form className="modal-body" onSubmit={handleSubmit}>
          <div className="import-form">
            <label>
              Job URL *
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://linkedin.com/jobs/view/..."
                required
                id="import-url"
              />
            </label>

            <label>
              Source
              <select
                className="filter-select"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                style={{ width: '100%' }}
              >
                <option value="linkedin">LinkedIn</option>
                <option value="wellfound">Wellfound (AngelList)</option>
                <option value="internshala">Internshala</option>
                <option value="manual">Other</option>
              </select>
            </label>

            <label>
              Job Title
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Junior Full-Stack Developer"
              />
            </label>

            <label>
              Company
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Acme Corp"
              />
            </label>

            <label>
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Paste the job description here (optional, helps with matching)..."
              />
            </label>

            {error && (
              <div style={{
                padding: 12,
                background: 'var(--color-danger-dim)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-danger)',
                fontSize: 13,
              }}>
                ⚠️ {error}
              </div>
            )}
          </div>

          <div className="modal-footer" style={{ padding: '16px 0 0' }}>
            <button className="btn btn-ghost" type="button" onClick={onClose}>Cancel</button>
            <button className="btn btn-primary" type="submit" disabled={loading || !url}>
              {loading ? <><span className="btn-spinner" /> Importing...</> : '➕ Import Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
