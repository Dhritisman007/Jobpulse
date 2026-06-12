const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Jobs
export const fetchJobs = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      query.append(key, value);
    }
  });
  return request(`/jobs?${query.toString()}`);
};

export const fetchJob = (id) => request(`/jobs/${id}`);

export const refreshJobs = () => request('/jobs/refresh', { method: 'POST' });

export const importJob = (data) =>
  request('/jobs/import', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const fetchSources = () => request('/jobs/sources');
export const fetchStats = () => request('/jobs/stats');

// Applications
export const updateApplication = (jobId, data) =>
  request(`/applications/${jobId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const fetchApplications = (status = null) => {
  const query = status ? `?status=${status}` : '';
  return request(`/applications${query}`);
};

export const deleteApplication = (jobId) =>
  request(`/applications/${jobId}`, { method: 'DELETE' });

// Cover Letters
export const generateCoverLetter = (jobId) =>
  request('/cover-letters/generate', {
    method: 'POST',
    body: JSON.stringify({ job_id: jobId }),
  });

// Admin
export const rescoreAll = () => request('/rescore', { method: 'POST' });
export const triggerNotification = () => request('/notify', { method: 'POST' });
