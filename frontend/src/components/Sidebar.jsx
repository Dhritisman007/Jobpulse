const CATEGORIES = [
  { key: null, label: 'All Jobs', icon: '📋' },
  { key: 'fullstack', label: 'Full-Stack', icon: '🌐' },
  { key: 'ml_ds', label: 'ML / Data Science', icon: '🤖' },
  { key: 'fintech', label: 'FinTech / Quant', icon: '💹' },
  { key: 'blockchain', label: 'Blockchain / Web3', icon: '⛓️' },
  { key: 'data_analysis', label: 'Data Analysis', icon: '📊' },
  { key: 'other', label: 'Other', icon: '📌' },
];

const STATUS_FILTERS = [
  { key: null, label: 'All Statuses', icon: '🔘' },
  { key: 'none', label: 'Untracked', icon: '⬜' },
  { key: 'interested', label: 'Interested', icon: '⭐' },
  { key: 'applied', label: 'Applied', icon: '✅' },
  { key: 'interview', label: 'Interview', icon: '💬' },
  { key: 'skipped', label: 'Skipped', icon: '⏭️' },
];

const PAGES = [
  { key: 'dashboard', label: 'Dashboard', icon: '📊' },
  { key: 'applications', label: 'Applications', icon: '📝' },
];

export default function Sidebar({
  currentPage,
  onPageChange,
  selectedCategory,
  onCategoryChange,
  selectedStatus,
  onStatusChange,
  sources,
  selectedSource,
  onSourceChange,
}) {
  return (
    <aside className="sidebar" id="sidebar">
      {/* Navigation */}
      <div className="sidebar-section">
        <div className="sidebar-label">Navigation</div>
        {PAGES.map((page) => (
          <div
            key={page.key}
            className={`sidebar-item ${currentPage === page.key ? 'active' : ''}`}
            onClick={() => onPageChange(page.key)}
          >
            <span>{page.icon}</span>
            <span>{page.label}</span>
          </div>
        ))}
      </div>

      {/* Categories */}
      <div className="sidebar-section">
        <div className="sidebar-label">Categories</div>
        {CATEGORIES.map((cat) => (
          <div
            key={cat.key || 'all'}
            className={`sidebar-item ${selectedCategory === cat.key ? 'active' : ''}`}
            onClick={() => onCategoryChange(cat.key)}
          >
            <span>{cat.icon}</span>
            <span>{cat.label}</span>
          </div>
        ))}
      </div>

      {/* Status */}
      <div className="sidebar-section">
        <div className="sidebar-label">Status</div>
        {STATUS_FILTERS.map((s) => (
          <div
            key={s.key || 'all'}
            className={`sidebar-item ${selectedStatus === s.key ? 'active' : ''}`}
            onClick={() => onStatusChange(s.key)}
          >
            <span>{s.icon}</span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className="sidebar-section">
          <div className="sidebar-label">Sources</div>
          <div
            className={`sidebar-item ${!selectedSource ? 'active' : ''}`}
            onClick={() => onSourceChange(null)}
          >
            <span>🌍</span>
            <span>All Sources</span>
          </div>
          {sources.map((src) => (
            <div
              key={src.source}
              className={`sidebar-item ${selectedSource === src.source ? 'active' : ''}`}
              onClick={() => onSourceChange(src.source)}
            >
              <span>🔗</span>
              <span>{src.source}</span>
              <span className="sidebar-item-count">{src.count}</span>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
