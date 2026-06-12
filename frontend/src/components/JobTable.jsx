import { ScoreBadge, StatusBadge, SourceBadge } from './StatusBadge';
import { updateApplication } from '../api';

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now - d;
  const diffHrs = diffMs / (1000 * 60 * 60);
  if (diffHrs < 1) return 'Just now';
  if (diffHrs < 24) return `${Math.floor(diffHrs)}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function JobTable({ jobs, onStatusUpdate, onGenerateCoverLetter, loading }) {
  const handleStatusChange = async (jobId, status) => {
    try {
      await updateApplication(jobId, { status });
      onStatusUpdate?.();
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  if (loading) {
    return (
      <div className="job-table-wrapper">
        <div className="empty-state loading-pulse">
          <div className="empty-state-icon">⏳</div>
          <div className="empty-state-title">Loading jobs...</div>
        </div>
      </div>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <div className="job-table-wrapper">
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <div className="empty-state-title">No jobs found</div>
          <div className="empty-state-text">
            Try adjusting your filters, or click "Refresh Jobs" to scan for new listings.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="job-table-wrapper">
      <table className="job-table" id="job-table">
        <thead>
          <tr>
            <th style={{ width: '35%' }}>Job</th>
            <th style={{ width: '10%' }}>Score</th>
            <th style={{ width: '10%' }}>Source</th>
            <th style={{ width: '10%' }}>Date</th>
            <th style={{ width: '10%' }}>Status</th>
            <th style={{ width: '25%' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>
                <div className="job-title-cell">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="job-title"
                  >
                    {job.title}
                  </a>
                  <span className="job-company">🏢 {job.company}</span>
                  <span className="job-location">📍 {job.location}</span>
                  {job.salary_range && (
                    <span className="job-location">💰 {job.salary_range}</span>
                  )}
                  {job.tags && job.tags.length > 0 && (
                    <div className="job-tags">
                      {job.tags.slice(0, 4).map((tag, i) => (
                        <span className="job-tag" key={i}>{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              </td>
              <td>
                <ScoreBadge score={job.match_score} />
              </td>
              <td>
                <SourceBadge source={job.source} />
              </td>
              <td>
                <span className="job-location">{formatDate(job.posted_date)}</span>
              </td>
              <td>
                <StatusBadge status={job.application_status} />
              </td>
              <td>
                <div className="job-actions">
                  {job.application_status !== 'applied' && (
                    <button
                      className="btn btn-sm btn-success"
                      onClick={() => handleStatusChange(job.id, 'applied')}
                      title="Mark as Applied"
                    >
                      ✅ Applied
                    </button>
                  )}
                  {job.application_status !== 'interested' && (
                    <button
                      className="btn btn-sm btn-warning"
                      onClick={() => handleStatusChange(job.id, 'interested')}
                      title="Mark as Interested"
                    >
                      ⭐
                    </button>
                  )}
                  {job.application_status !== 'skipped' && (
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => handleStatusChange(job.id, 'skipped')}
                      title="Skip"
                    >
                      ⏭️
                    </button>
                  )}
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => onGenerateCoverLetter(job)}
                    title="Generate Cover Letter"
                  >
                    ✍️
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
