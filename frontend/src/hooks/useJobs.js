import { useState, useEffect, useCallback } from 'react';
import { fetchJobs, fetchStats, fetchSources } from '../api';

export function useJobs(filters = {}) {
  const [data, setData] = useState({ jobs: [], total: 0, page: 1, per_page: 30 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchJobs(filters);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  return { ...data, loading, error, reload: loadJobs };
}

export function useStats() {
  const [stats, setStats] = useState({
    total_jobs: 0,
    total_applied: 0,
    total_interested: 0,
    avg_match_score: 0,
  });
  const [loading, setLoading] = useState(true);

  const loadStats = useCallback(async () => {
    try {
      const result = await fetchStats();
      setStats(result);
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return { stats, loading, reload: loadStats };
}

export function useSources() {
  const [sources, setSources] = useState([]);

  useEffect(() => {
    fetchSources()
      .then(setSources)
      .catch(console.error);
  }, []);

  return sources;
}
