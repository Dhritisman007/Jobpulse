export default function Header({ onRefresh, isRefreshing, lastUpdated }) {
  return (
    <header className="header" id="app-header">
      <div className="header-left">
        <div>
          <div className="header-logo">⚡ JobPulse</div>
          <div className="header-subtitle">Remote Job Search Automation</div>
        </div>
      </div>
      <div className="header-right">
        {lastUpdated && (
          <span className="header-timestamp">
            Last updated: {new Date(lastUpdated).toLocaleString()}
          </span>
        )}
        <button
          className="btn btn-primary"
          onClick={onRefresh}
          disabled={isRefreshing}
          id="refresh-btn"
        >
          {isRefreshing ? (
            <>
              <span className="btn-spinner" />
              Scanning...
            </>
          ) : (
            <>🔄 Refresh Jobs</>
          )}
        </button>
      </div>
    </header>
  );
}
