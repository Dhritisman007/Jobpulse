import { useState, useEffect } from 'react';
import { fetchApplications, updateApplication, deleteApplication } from '../api';
import { StatusBadge } from '../components/StatusBadge';

const TABS = [
  { key: null, label: 'All' },
  { key: 'applied', label: 'Applied' },
  { key: 'interested', label: 'Interested' },
  { key: 'interview', label: 'Interview' },
  { key: 'skipped', label: 'Skipped' },
];

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function ApplicationLog() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(null);
  const [editingNotes, setEditingNotes] = useState(null);
  const [notesText, setNotesText] = useState('');

  const loadApplications = async () => {
    setLoading(true);
    try {
      const data = await fetchApplications(activeTab);
      setApplications(data);
    } catch (err) {
      console.error('Failed to load applications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, [activeTab]);

  const handleStatusChange = async (jobId, status) => {
    try {
      await updateApplication(jobId, { status });
      loadApplications();
    } catch (err) {
      console.error('Failed to update:', err);
    }
  };

  const handleSaveNotes = async (jobId) => {
    try {
      await updateApplication(jobId, {
        status: applications.find(a => a.job_id === jobId)?.status || 'interested',
        notes: notesText,
      });
      setEditingNotes(null);
      loadApplications();
    } catch (err) {
      console.error('Failed to save notes:', err);
    }
  };

  const handleDelete = async (jobId) => {
    if (!confirm('Remove tracking for this job?')) return;
    try {
      await deleteApplication(jobId);
      loadApplications();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  return (
    <>
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>
        📝 Application Tracker
      </h2>

      {/* Tabs */}
      <div className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key || 'all'}
            className={`tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Application Cards */}
      {loading ? (
        <div className="empty-state loading-pulse">
          <div className="empty-state-icon">⏳</div>
          <div className="empty-state-title">Loading applications...</div>
        </div>
      ) : applications.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <div className="empty-state-title">No applications yet</div>
          <div className="empty-state-text">
            Mark jobs as "Applied" or "Interested" from the Dashboard to start tracking.
          </div>
        </div>
      ) : (
        applications.map((app) => (
          <div className="app-log-card" key={app.id}>
            <div className="app-log-header">
              <div>
                <a
                  href={app.job?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ fontSize: 15, fontWeight: 600 }}
                >
                  {app.job?.title || 'Unknown Job'}
                </a>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginTop: 2 }}>
                  🏢 {app.job?.company} • 📍 {app.job?.location}
                  {app.job?.match_score != null && (
                    <> • 📊 Score: <strong>{Math.round(app.job.match_score)}</strong></>
                  )}
                </div>
              </div>
              <StatusBadge status={app.status} />
            </div>

            <div className="app-log-meta">
              <span>🔗 {app.job?.source}</span>
              {app.applied_date && <span>📅 Applied: {formatDate(app.applied_date)}</span>}
              <span>🕐 Updated: {formatDate(app.updated_at)}</span>
            </div>

            {/* Notes */}
            {editingNotes === app.job_id ? (
              <div style={{ marginTop: 8 }}>
                <textarea
                  className="cover-letter-text"
                  value={notesText}
                  onChange={(e) => setNotesText(e.target.value)}
                  rows={3}
                  style={{ minHeight: 60 }}
                  placeholder="Add notes about this application..."
                />
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => handleSaveNotes(app.job_id)}
                  >
                    💾 Save
                  </button>
                  <button
                    className="btn btn-sm btn-ghost"
                    onClick={() => setEditingNotes(null)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : app.notes ? (
              <div
                className="app-log-notes"
                onClick={() => { setEditingNotes(app.job_id); setNotesText(app.notes); }}
                style={{ cursor: 'pointer' }}
                title="Click to edit"
              >
                📌 {app.notes}
              </div>
            ) : null}

            {/* Cover Letter Preview */}
            {app.cover_letter_text && (
              <details style={{ marginTop: 8 }}>
                <summary style={{
                  color: 'var(--color-text-muted)',
                  fontSize: 12,
                  cursor: 'pointer',
                }}>
                  ✍️ Cover letter generated
                </summary>
                <div style={{
                  marginTop: 8,
                  padding: 12,
                  background: 'var(--color-bg-input)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 13,
                  lineHeight: 1.7,
                  color: 'var(--color-text-secondary)',
                  whiteSpace: 'pre-wrap',
                }}>
                  {app.cover_letter_text}
                </div>
              </details>
            )}

            {/* Actions */}
            <div style={{ display: 'flex', gap: 4, marginTop: 12 }}>
              {app.status !== 'applied' && (
                <button
                  className="btn btn-sm btn-success"
                  onClick={() => handleStatusChange(app.job_id, 'applied')}
                >
                  ✅ Applied
                </button>
              )}
              {app.status !== 'interview' && app.status === 'applied' && (
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => handleStatusChange(app.job_id, 'interview')}
                >
                  💬 Interview
                </button>
              )}
              <button
                className="btn btn-sm btn-ghost"
                onClick={() => { setEditingNotes(app.job_id); setNotesText(app.notes || ''); }}
              >
                📝 Notes
              </button>
              <button
                className="btn btn-sm btn-danger"
                onClick={() => handleDelete(app.job_id)}
                style={{ marginLeft: 'auto' }}
              >
                🗑️
              </button>
            </div>
          </div>
        ))
      )}
    </>
  );
}
