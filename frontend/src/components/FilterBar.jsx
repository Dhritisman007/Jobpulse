export default function FilterBar({ search, onSearchChange, sortBy, onSortChange, onImportClick }) {
  return (
    <div className="filter-bar" id="filter-bar">
      <div className="filter-search">
        <span className="filter-search-icon">🔍</span>
        <input
          type="text"
          className="filter-search-input"
          placeholder="Search jobs by title, company, or keyword..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          id="search-input"
        />
      </div>

      <select
        className="filter-select"
        value={sortBy}
        onChange={(e) => onSortChange(e.target.value)}
        id="sort-select"
      >
        <option value="match_score">Sort by Score</option>
        <option value="posted_date">Sort by Date</option>
        <option value="company">Sort by Company</option>
        <option value="title">Sort by Title</option>
      </select>

      <button className="btn btn-secondary" onClick={onImportClick} id="import-btn">
        ➕ Import Job
      </button>
    </div>
  );
}
