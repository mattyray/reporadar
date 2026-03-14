const API_BASE = '/api';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    ...options.headers as Record<string, string>,
  };

  if (token && token !== 'session') {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'Request failed');
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

export const api = {
  // Accounts
  getProfile: () => request<import('../types/api').UserProfile>('/accounts/me/'),
  // Search
  createSearch: (config: import('../types/api').SearchConfig) =>
    request<import('../types/api').SearchQuery>('/search/', {
      method: 'POST',
      body: JSON.stringify(config),
    }),
  getSearchStatus: (id: string) =>
    request<import('../types/api').SearchQuery>(`/search/${id}/status/`),
  getSearchResults: (id: string) =>
    request<{ results: import('../types/api').SearchResult[] }>(`/search/${id}/results/`),
  getSearchHistory: () =>
    request<{ results: import('../types/api').SearchQuery[] }>('/search/history/'),

  // Company Lookup
  searchCompany: (q: string) =>
    request<{ results: import('../types/api').CompanyLookupResult[] }>(`/search/company/?q=${encodeURIComponent(q)}`),
  scanCompany: (login: string) =>
    request<{ detail: string; task_id: string; login: string }>('/search/company/scan/', {
      method: 'POST',
      body: JSON.stringify({ login }),
    }),
  getCompanyScanStatus: (login: string) =>
    request<import('../types/api').CompanyScanResponse>(`/search/company/scan/status/?login=${encodeURIComponent(login)}`),

  // Prospects
  getProspects: () =>
    request<{ results: import('../types/api').Organization[] }>('/prospects/'),
  getProspect: (id: number) =>
    request<import('../types/api').Organization>(`/prospects/${id}/`),
  saveProspect: (id: number) =>
    request(`/prospects/${id}/save/`, { method: 'POST' }),
  getSavedProspects: () => request('/prospects/saved/'),
  removeSavedProspect: (id: number) =>
    request(`/prospects/saved/${id}/`, { method: 'DELETE' }),

  // Repo Analysis
  analyzeRepo: (repoId: number) =>
    request<{ detail: string; status: string }>(`/prospects/repos/${repoId}/analyze/`, { method: 'POST' }),
  getRepoAnalysis: (repoId: number) =>
    request<import('../types/api').Repo>(`/prospects/repos/${repoId}/analyze/`),

  // Resumes
  uploadResume: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/resumes/upload/', { method: 'POST', body: formData });
  },
  getResumeProfile: () => request<import('../types/api').ResumeProfile>('/resumes/profile/'),
  deleteResume: () => request('/resumes/profile/', { method: 'DELETE' }),

  // Jobs
  getOrgJobs: (orgId: number) =>
    request<{ results: import('../types/api').JobListing[] }>(`/jobs/org/${orgId}/`),
  checkOrgJobs: (orgId: number) =>
    request<import('../types/api').JobCheckResponse>(`/jobs/org/${orgId}/check/`, { method: 'POST' }),
  searchJobs: (params: { techs?: string; location?: string; department?: string; title?: string; days?: string; source?: string; remote?: string }) => {
    const query = new URLSearchParams();
    if (params.techs) query.set('techs', params.techs);
    if (params.location) query.set('location', params.location);
    if (params.department) query.set('department', params.department);
    if (params.title) query.set('title', params.title);
    if (params.days) query.set('days', params.days);
    if (params.source) query.set('source', params.source);
    if (params.remote) query.set('remote', params.remote);
    return request<{ count: number; results: import('../types/api').JobListing[] }>(`/jobs/?${query.toString()}`);
  },

  // Resume matching
  getMatchedJobs: () =>
    request<{ count: number; results: (import('../types/api').JobListing & { match_score: number; matched_techs: string[] })[] }>('/resumes/matched-jobs/'),
  triggerRematching: () =>
    request<{ matched: number }>('/resumes/matched-jobs/', { method: 'POST' }),
};
