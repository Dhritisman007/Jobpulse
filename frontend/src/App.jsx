import { useState, useCallback } from 'react';
import { useSources } from './hooks/useJobs';
import { refreshJobs } from './api';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ApplicationLog from './pages/ApplicationLog';

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [toasts, setToasts] = useState([]);

  // Filters
  const [filters, setFilters] = useState({
    category: null,
    source: null,
    status: null,
    search: '',
    sort_by: 'match_score',
    sort_order: 'desc',
    days_ago: 30,
    page: 1,
    per_page: 30,
  });

  const sources = useSources();

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    addToast('🔄 Scanning all job sources...', 'info');
    try {
      const result = await refreshJobs();
      setLastUpdated(new Date().toISOString());
      addToast(
        `✅ Found ${result.total_jobs_found} jobs, ${result.total_new_jobs} new!`,
        'success'
      );
      // Force re-render by updating a filter value slightly
      setFilters((prev) => ({ ...prev, page: 1 }));
    } catch (err) {
      addToast(`❌ Refresh failed: ${err.message}`, 'error');
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, []);

  return (
    <div className="app-layout">
      <Sidebar
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        selectedCategory={filters.category}
        onCategoryChange={(cat) => handleFilterChange({ ...filters, category: cat, page: 1 })}
        selectedStatus={filters.status}
        onStatusChange={(status) => handleFilterChange({ ...filters, status: status, page: 1 })}
        sources={sources}
        selectedSource={filters.source}
        onSourceChange={(source) => handleFilterChange({ ...filters, source: source, page: 1 })}
      />

      <div className="app-main">
        <Header
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          lastUpdated={lastUpdated}
        />

        <div className="app-content">
          {currentPage === 'dashboard' && (
            <Dashboard
              filters={filters}
              onFilterChange={handleFilterChange}
            />
          )}
          {currentPage === 'applications' && (
            <ApplicationLog />
          )}
        </div>
      </div>

      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}
