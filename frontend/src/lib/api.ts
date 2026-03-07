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
  getApiKeys: () => request<any[]>('/accounts/api-keys/'),
  addApiKey: (provider: string, apiKey: string) =>
    request('/accounts/api-keys/', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key: apiKey }),
    }),
  deleteApiKey: (provider: string) =>
    request(`/accounts/api-keys/${provider}/`, { method: 'DELETE' }),
  getApiKeyStatus: () => request('/accounts/api-keys/status/'),

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

  // Enrichment
  enrichOrg: (orgId: number) =>
    request(`/enrichment/${orgId}/enrich/`, { method: 'POST' }),
  getContacts: (orgId: number) =>
    request<import('../types/api').Contact[]>(`/enrichment/${orgId}/contacts/`),

  // Resumes
  uploadResume: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/resumes/upload/', { method: 'POST', body: formData });
  },
  getResumeProfile: () => request<import('../types/api').ResumeProfile>('/resumes/profile/'),
  deleteResume: () => request('/resumes/profile/', { method: 'DELETE' }),

  // Outreach
  generateOutreach: (orgId: number, messageType: string, contactId?: number) =>
    request<import('../types/api').OutreachMessage>('/outreach/generate/', {
      method: 'POST',
      body: JSON.stringify({
        organization_id: orgId,
        message_type: messageType,
        ...(contactId && { contact_id: contactId }),
      }),
    }),
  getOutreachHistory: () =>
    request<{ results: import('../types/api').OutreachMessage[] }>('/outreach/history/'),

  // Jobs
  getOrgJobs: (orgId: number) =>
    request<{ results: import('../types/api').JobListing[] }>(`/jobs/org/${orgId}/`),
  checkOrgJobs: (orgId: number) =>
    request<import('../types/api').JobCheckResponse>(`/jobs/org/${orgId}/check/`, { method: 'POST' }),
  searchJobs: (params: { techs?: string; location?: string; department?: string; title?: string }) => {
    const query = new URLSearchParams();
    if (params.techs) query.set('techs', params.techs);
    if (params.location) query.set('location', params.location);
    if (params.department) query.set('department', params.department);
    if (params.title) query.set('title', params.title);
    return request<{ results: import('../types/api').JobListing[] }>(`/jobs/?${query.toString()}`);
  },
};
