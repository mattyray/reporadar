import { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { SearchConfig, SearchQuery, SearchResult, CompanyLookupResult } from '../types/api';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import TechChipSelector from '../components/TechChipSelector';
import TechChip from '../components/TechChip';
import SetupChecklist from '../components/SetupChecklist';

function formatTimeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getSearchLabel(search: SearchQuery): string {
  if (search.name) return search.name;
  const techs = search.config?.stack_requirements?.must_have;
  if (techs?.length) {
    const display = techs.slice(0, 3).join(', ');
    return techs.length > 3 ? `${display} +${techs.length - 3}` : display;
  }
  return 'Search';
}

function SearchStatus({ search, compact }: { search: SearchQuery; compact?: boolean }) {
  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const isActive = search.status === 'pending' || search.status === 'running';

  if (compact) {
    return (
      <div className="flex items-center justify-between bg-white rounded-lg shadow p-3 hover:bg-gray-50">
        <div className="flex items-center gap-3 min-w-0">
          <div className="min-w-0">
            <span className="font-medium text-gray-900 text-sm">{getSearchLabel(search)}</span>
            <div className="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
              <span>{search.total_orgs_found} orgs</span>
              <span>{formatTimeAgo(search.created_at)}</span>
            </div>
          </div>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${statusColors[search.status]}`}>
          {search.status}
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="font-medium text-gray-900">{getSearchLabel(search)}</span>
          <span className="ml-2 text-sm text-gray-500">
            {search.total_orgs_found} orgs found
          </span>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[search.status]}`}>
          {search.status}
        </span>
      </div>
      {isActive && (
        <div className="mt-3 flex items-center gap-2 text-sm text-blue-700 bg-blue-50 rounded-md px-3 py-2">
          <svg className="animate-spin h-4 w-4 text-blue-500 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>
            Scanning GitHub repos, detecting tech stacks, and checking for open roles — this usually takes 3-5 minutes. You can leave this page and come back.
          </span>
        </div>
      )}
    </div>
  );
}

function SearchResultsList({ searchId }: { searchId: string }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data } = useQuery({
    queryKey: ['searchResults', searchId],
    queryFn: () => api.getSearchResults(searchId),
  });

  if (!data?.results?.length) return <p className="text-gray-500 text-sm">No results yet.</p>;

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">Click a company to see their repos, tech stack, and team.</p>

      {/* Contextual prompt: connect GitHub for more results */}
      {!user?.github_connected && (
        <div className="flex items-center justify-between bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-sm text-yellow-800">
            These are demo results. Connect GitHub to search 28M+ real repos.
          </p>
          <a
            href={`https://reporadar-production.up.railway.app/api/auth/github/start/?token=${localStorage.getItem('auth_token') || ''}`}
            className="flex-shrink-0 bg-gray-900 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-gray-800"
          >
            Connect GitHub
          </a>
        </div>
      )}

      {data.results.map((r: SearchResult) => (
        <div
          key={r.id}
          onClick={() => navigate(`/prospects/${r.organization_id}`)}
          className="flex items-center justify-between bg-white rounded-lg shadow p-4 cursor-pointer hover:bg-gray-50"
        >
          <div className="flex items-center gap-3">
            {r.organization_avatar && (
              <img src={r.organization_avatar} alt="" className="w-8 h-8 rounded-full" />
            )}
            <div>
              <span className="font-medium text-gray-900">{r.organization_name}</span>
              {r.is_hiring && (
                <span className="ml-2 px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-xs font-medium">
                  Hiring
                </span>
              )}
              <span className="ml-2 text-sm text-gray-500">{r.repo_name}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex flex-wrap gap-1 items-center">
              {r.matched_stack.map((tech) => (
                <TechChip key={tech} name={tech} category="backend" />
              ))}
              {r.matched_ai_tools?.length > 0 && r.matched_stack.length > 0 && (
                <span className="text-gray-300 mx-0.5">|</span>
              )}
              {r.matched_ai_tools?.map((tool) => (
                <TechChip key={tool} name={tool} category="ai_tool" />
              ))}
              {r.matched_infra?.length > 0 && (r.matched_stack.length > 0 || r.matched_ai_tools?.length > 0) && (
                <span className="text-gray-300 mx-0.5">|</span>
              )}
              {r.matched_infra?.map((item) => (
                <TechChip key={item} name={item} category="infra" />
              ))}
            </div>
            <span className="text-sm font-semibold text-indigo-600">{r.match_score}%</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function CompanySearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [scanningLogin, setScanningLogin] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  const { data: lookupResults, isFetching } = useQuery({
    queryKey: ['companyLookup', query],
    queryFn: () => api.searchCompany(query),
    enabled: query.length >= 2,
    staleTime: 30000,
  });

  // Poll for scan completion
  const { data: scanStatus } = useQuery({
    queryKey: ['companyScan', scanningLogin],
    queryFn: () => api.getCompanyScanStatus(scanningLogin!),
    enabled: !!scanningLogin,
    refetchInterval: (q) => {
      if (q.state.data?.status === 'completed') return false;
      return 3000;
    },
  });

  // Navigate when scan completes
  useEffect(() => {
    if (scanStatus?.status === 'completed' && scanStatus.organization) {
      setScanningLogin(null);
      navigate(`/prospects/${scanStatus.organization.id}`);
    }
  }, [scanStatus, navigate]);

  const scanCompany = useMutation({
    mutationFn: (login: string) => api.scanCompany(login),
    onSuccess: (_data, login) => {
      setScanningLogin(login);
      setShowResults(false);
    },
  });

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setShowResults(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const results = lookupResults?.results ?? [];

  return (
    <div ref={ref} className="relative">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowResults(true);
            }}
            onFocus={() => query.length >= 2 && setShowResults(true)}
            placeholder="Search by company name (e.g. ycharts, stripe, vercel)"
            className="w-full border border-gray-300 rounded-md px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
          {isFetching && (
            <div className="absolute right-3 top-3">
              <svg className="animate-spin h-4 w-4 text-gray-400" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          )}
        </div>
      </div>

      {/* Scanning indicator */}
      {scanningLogin && (
        <div className="mt-2 flex items-center gap-2 text-sm text-blue-700 bg-blue-50 rounded-md px-3 py-2">
          <svg className="animate-spin h-4 w-4 text-blue-500 flex-shrink-0" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Scanning <strong>{scanningLogin}</strong> — pulling repos, detecting tech stacks, checking for open roles. This takes about a minute...</span>
        </div>
      )}

      {/* Dropdown results */}
      {showResults && query.length >= 2 && results.length > 0 && (
        <div className="absolute z-10 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 max-h-80 overflow-y-auto">
          {results.map((r: CompanyLookupResult) => (
            <button
              key={r.github_id}
              onClick={() => scanCompany.mutate(r.login)}
              disabled={scanCompany.isPending}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 text-left cursor-pointer border-b border-gray-100 last:border-0"
            >
              <img src={r.avatar_url} alt="" className="w-8 h-8 rounded-full" />
              <div className="min-w-0">
                <span className="font-medium text-sm text-gray-900">{r.login}</span>
                <span className="ml-2 px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">
                  {r.type}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {showResults && query.length >= 2 && !isFetching && results.length === 0 && (
        <div className="absolute z-10 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 p-4 text-sm text-gray-500 text-center">
          No GitHub organizations found for "{query}"
        </div>
      )}
    </div>
  );
}

const AI_TOOL_OPTIONS = [
  { label: 'Claude Code', value: 'CLAUDE.md' },
  { label: 'Cursor', value: '.cursor' },
  { label: 'GitHub Copilot', value: '.github/copilot' },
  { label: 'Windsurf', value: '.windsurfrules' },
  { label: 'Aider', value: '.aider' },
  { label: 'Codeium', value: '.codeium' },
  { label: 'Continue.dev', value: '.continue' },
  { label: 'Bolt.new', value: '.bolt' },
  { label: 'Vercel v0', value: '.v0' },
  { label: 'Lovable', value: '.lovable' },
  { label: 'Google IDX', value: '.idx' },
  { label: 'Amazon Q', value: '.amazonq' },
  { label: 'Cline', value: '.cline' },
  { label: 'Roo Code', value: '.roo' },
  { label: 'Codex', value: 'codex.md' },
];

export default function SearchPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [activeSearchId, setActiveSearchId] = useState<string | null>(null);
  const [selectedTechs, setSelectedTechs] = useState<string[]>([]);
  const [selectedAiTools, setSelectedAiTools] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [minStars, setMinStars] = useState(0);
  const [minContributors, setMinContributors] = useState(2);
  const [maxResults, setMaxResults] = useState(50);

  const { data: history } = useQuery({
    queryKey: ['searchHistory'],
    queryFn: api.getSearchHistory,
  });

  const { data: prospects } = useQuery({
    queryKey: ['prospects'],
    queryFn: api.getProspects,
  });

  const { data: activeSearch } = useQuery({
    queryKey: ['searchStatus', activeSearchId],
    queryFn: () => api.getSearchStatus(activeSearchId!),
    enabled: !!activeSearchId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'running' ? 3000 : false;
    },
  });

  const createSearch = useMutation({
    mutationFn: api.createSearch,
    onSuccess: (data) => {
      setActiveSearchId(data.id);
      queryClient.invalidateQueries({ queryKey: ['searchHistory'] });
    },
  });

  const handleSearch = () => {
    if (selectedTechs.length === 0 && selectedAiTools.length === 0) return;
    const config: SearchConfig = {
      stack_requirements: {
        must_have: selectedTechs,
        ai_tool_signals: selectedAiTools.length > 0 ? selectedAiTools : undefined,
      },
      filters: {
        org_only: true,
        min_stars: minStars,
        min_contributors: minContributors,
      },
      max_results: maxResults,
    };
    createSearch.mutate(config);
  };

  const recentProspects = prospects?.results?.slice(0, 6) ?? [];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Companies</h1>
        <p className="text-gray-500 mt-1">
          Search GitHub organizations by tech stack to find companies building with the same tools.
        </p>
      </div>

      <SetupChecklist />

      {/* Company lookup — search by name */}
      {user?.github_connected && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-1">Look up a specific company</h2>
          <p className="text-xs text-gray-500 mb-3">Type a company or GitHub org name to scan their repos and tech stack.</p>
          <CompanySearch />
        </div>
      )}

      {/* Tech chip selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <TechChipSelector
          selected={selectedTechs}
          onChange={setSelectedTechs}
          label="What technologies do you work with?"
          hint="Click to select, or type your own below."
        />

        {/* AI Tool selector */}
        <div className="mt-4 pt-4 border-t border-gray-100">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What AI tools should they build with?
          </label>
          <p className="text-xs text-gray-400 mb-2">Optional — find companies using specific AI coding tools.</p>
          <div className="flex flex-wrap gap-2">
            {AI_TOOL_OPTIONS.map((tool) => {
              const isSelected = selectedAiTools.includes(tool.value);
              return (
                <button
                  key={tool.value}
                  type="button"
                  onClick={() =>
                    setSelectedAiTools((prev) =>
                      isSelected ? prev.filter((v) => v !== tool.value) : [...prev, tool.value]
                    )
                  }
                  className={`px-3 py-1.5 rounded-full text-xs font-medium cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-purple-600 text-white'
                      : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
                  }`}
                >
                  {tool.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Advanced filters (collapsed) */}
        <div className="mt-4 pt-4 border-t border-gray-100">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            type="button"
            className="text-xs text-indigo-600 hover:underline cursor-pointer"
          >
            {showAdvanced ? 'Hide advanced filters' : 'Advanced filters'}
          </button>

          {showAdvanced && (
            <div className="grid grid-cols-3 gap-4 mt-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min stars</label>
                <input
                  type="number"
                  value={minStars}
                  onChange={(e) => setMinStars(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min contributors</label>
                <input
                  type="number"
                  value={minContributors}
                  onChange={(e) => setMinContributors(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max results</label>
                <input
                  type="number"
                  value={maxResults}
                  onChange={(e) => setMaxResults(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
            </div>
          )}
        </div>

        {/* Search button */}
        <button
          onClick={handleSearch}
          disabled={(selectedTechs.length === 0 && selectedAiTools.length === 0) || createSearch.isPending || (activeSearch && (activeSearch.status === 'pending' || activeSearch.status === 'running'))}
          className="mt-4 w-full bg-indigo-600 text-white rounded-md py-2.5 px-4 font-medium hover:bg-indigo-700 disabled:opacity-50 cursor-pointer"
        >
          {createSearch.isPending
            ? 'Searching...'
            : (selectedTechs.length === 0 && selectedAiTools.length === 0)
              ? 'Select technologies or AI tools'
              : `Find Companies Using ${[...selectedTechs.slice(0, 3), ...selectedAiTools.length > 0 ? [`${selectedAiTools.length} AI tool${selectedAiTools.length > 1 ? 's' : ''}`] : []].join(', ')}${selectedTechs.length > 3 ? ' +more' : ''}`}
        </button>
      </div>

      {createSearch.isError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
          {createSearch.error.message}
        </div>
      )}

      {/* Active search results */}
      {activeSearch && (
        <div className="space-y-4">
          <SearchStatus search={activeSearch} />
          {activeSearch.status === 'completed' && (
            <SearchResultsList searchId={activeSearch.id} />
          )}
        </div>
      )}

      {/* Recent discoveries */}
      {recentProspects.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Recent Discoveries</h3>
            <button
              onClick={() => navigate('/companies')}
              className="text-xs text-indigo-600 hover:underline cursor-pointer"
            >
              View all
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {recentProspects.map((org: any) => (
              <div
                key={org.id}
                onClick={() => navigate(`/prospects/${org.id}`)}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-gray-50 cursor-pointer"
              >
                {org.avatar_url && <img src={org.avatar_url} alt="" className="w-6 h-6 rounded-full" />}
                <span className="text-sm text-gray-700 truncate">{org.name || org.github_login}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Past searches — show last 5, exclude currently active */}
      {history?.results && history.results.filter((s: SearchQuery) => s.id !== activeSearchId).length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-900">Past Searches</h3>
          {history.results
            .filter((s: SearchQuery) => s.id !== activeSearchId)
            .slice(0, 5)
            .map((s: SearchQuery) => (
              <div
                key={s.id}
                onClick={() => setActiveSearchId(s.id)}
                className="cursor-pointer"
              >
                <SearchStatus search={s} compact />
              </div>
            ))}
          {history.results.filter((s: SearchQuery) => s.id !== activeSearchId).length > 5 && (
            <p className="text-xs text-gray-400 text-center pt-1">
              Showing 5 of {history.results.filter((s: SearchQuery) => s.id !== activeSearchId).length} searches
            </p>
          )}
        </div>
      )}
    </div>
  );
}
