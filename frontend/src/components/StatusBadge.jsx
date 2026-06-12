export function ScoreBadge({ score }) {
  if (score === null || score === undefined) {
    return <span className="score-badge score-low">—</span>;
  }

  const level = score >= 50 ? 'high' : score >= 30 ? 'medium' : 'low';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <span className={`score-badge score-${level}`}>{Math.round(score)}</span>
      <div className="score-bar">
        <div
          className={`score-bar-fill score-${level}`}
          style={{ width: `${Math.min(100, score)}%` }}
        />
      </div>
    </div>
  );
}

export function StatusBadge({ status }) {
  if (!status) return null;
  return (
    <span className={`status-badge status-${status}`}>
      {status}
    </span>
  );
}

export function SourceBadge({ source }) {
  return <span className="source-badge">{source}</span>;
}
