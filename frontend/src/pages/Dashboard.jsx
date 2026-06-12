import { useState, useCallback, useEffect } from 'react';
import { useJobs, useStats } from '../hooks/useJobs';
import FilterBar from '../components/FilterBar';
import JobTable from '../components/JobTable';
import CoverLetterModal from '../components/CoverLetterModal';
import ImportModal from '../components/ImportModal';

export default function Dashboard({ filters, onFilterChange }) {
  const { stats, reload: reloadStats } = useStats();
  const { jobs, total, loading, error, reload } = useJobs(filters);
  const [coverLetterJob, setCoverLetterJob] = useState(null);
  const [showImport, setShowImport] = useState(false);

  const handleStatusUpdate = useCallback(() => {
    reload();
    reloadStats();
  }, [reload, reloadStats]);

  return (
    <>
      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-value">{stats.total_jobs}</div>
          <div className="stat-card-label">Total Jobs</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-value" style={{
            background: 'linear-gradient(135deg, #10b981, #34d399)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>{stats.total_applied}</div>
          <div className="stat-card-label">Applied</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-value" style={{
            background: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>{stats.total_interested}</div>
          <div className="stat-card-label">Interested</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-value" style={{
            background: 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>{stats.avg_match_score}</div>
          <div className="stat-card-label">Avg Match Score</div>
        </div>
      </div>

      {/* Filters */}
      <FilterBar
        search={filters.search || ''}
        onSearchChange={(val) => onFilterChange({ ...filters, search: val, page: 1 })}
        sortBy={filters.sort_by || 'match_score'}
        onSortChange={(val) => onFilterChange({ ...filters, sort_by: val, page: 1 })}
        onImportClick={() => setShowImport(true)}
      />

      {/* Error */}
      {error && (
        <div style={{
          padding: 12,
          background: 'var(--color-danger-dim)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--color-danger)',
          fontSize: 13,
          marginBottom: 16,
        }}>
          ⚠️ Failed to load jobs: {error}
        </div>
      )}

      {/* Job Table */}
      <JobTable
        jobs={jobs}
        loading={loading}
        onStatusUpdate={handleStatusUpdate}
        onGenerateCoverLetter={setCoverLetterJob}
      />

      {/* Pagination */}
      {total > filters.per_page && (
        <div className="pagination">
          <button
            className="btn btn-sm btn-secondary"
            disabled={filters.page <= 1}
            onClick={() => onFilterChange({ ...filters, page: filters.page - 1 })}
          >
            ← Prev
          </button>
          <span className="pagination-info">
            Page {filters.page} of {Math.ceil(total / filters.per_page)} ({total} jobs)
          </span>
          <button
            className="btn btn-sm btn-secondary"
            disabled={filters.page >= Math.ceil(total / filters.per_page)}
            onClick={() => onFilterChange({ ...filters, page: filters.page + 1 })}
          >
            Next →
          </button>
        </div>
      )}

      {/* Modals */}
      {coverLetterJob && (
        <CoverLetterModal
          job={coverLetterJob}
          onClose={() => setCoverLetterJob(null)}
        />
      )}

      {showImport && (
        <ImportModal
          onClose={() => setShowImport(false)}
          onImported={() => {
            reload();
            reloadStats();
          }}
        />
      )}
    </>
  );
}
