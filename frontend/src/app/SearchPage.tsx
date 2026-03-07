import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { SearchConfig, SearchQuery, SearchResult } from '../types/api';
import { useNavigate } from 'react-router-dom';
import SetupChecklist from '../components/SetupChecklist';

function SearchForm({ onSubmit }: { onSubmit: (config: SearchConfig) => void }) {
  const [mustHave, setMustHave] = useState('');
  const [niceToHave, setNiceToHave] = useState('');
  const [aiSignals, setAiSignals] = useState('');
  const [minStars, setMinStars] = useState(0);
  const [minContributors, setMinContributors] = useState(2);
  const [maxResults, setMaxResults] = useState(50);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const config: SearchConfig = {
      stack_requirements: {
        must_have: mustHave.split(',').map((s) => s.trim()).filter(Boolean),
        nice_to_have: niceToHave.split(',').map((s) => s.trim()).filter(Boolean),
        ai_tool_signals: aiSignals.split(',').map((s) => s.trim()).filter(Boolean),
      },
      filters: {
        org_only: true,
        min_stars: minStars,
        min_contributors: minContributors,
      },
      max_results: maxResults,
    };
    onSubmit(config);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">New Search</h2>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Must-have technologies (comma separated)
        </label>
        <input
          type="text"
          value={mustHave}
          onChange={(e) => setMustHave(e.target.value)}
          placeholder="django, react, postgresql"
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Nice-to-have technologies (comma separated)
        </label>
        <input
          type="text"
          value={niceToHave}
          onChange={(e) => setNiceToHave(e.target.value)}
          placeholder="typescript, celery, redis"
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          AI tool signals (comma separated)
        </label>
        <input
          type="text"
          value={aiSignals}
          onChange={(e) => setAiSignals(e.target.value)}
          placeholder="CLAUDE.md, .cursor, .github/copilot"
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
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

      <button
        type="submit"
        className="w-full bg-indigo-600 text-white rounded-md py-2 px-4 font-medium hover:bg-indigo-700 cursor-pointer"
      >
        Start Search
      </button>
    </form>
  );
}

function SearchStatus({ search }: { search: SearchQuery }) {
  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <div className="flex items-center justify-between bg-white rounded-lg shadow p-4">
      <div>
        <span className="font-medium text-gray-900">
          {search.name || 'Search'}
        </span>
        <span className="ml-2 text-sm text-gray-500">
          {search.total_orgs_found} orgs found
        </span>
      </div>
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[search.status]}`}>
        {search.status}
      </span>
    </div>
  );
}

function SearchResultsList({ searchId }: { searchId: string }) {
  const navigate = useNavigate();
  const { data } = useQuery({
    queryKey: ['searchResults', searchId],
    queryFn: () => api.getSearchResults(searchId),
  });

  if (!data?.results?.length) return <p className="text-gray-500 text-sm">No results yet.</p>;

  return (
    <div className="space-y-2">
      {data.results.map((r: SearchResult) => (
        <div
          key={r.id}
          onClick={() => navigate(`/prospects/${r.id}`)}
          className="flex items-center justify-between bg-white rounded-lg shadow p-4 cursor-pointer hover:bg-gray-50"
        >
          <div className="flex items-center gap-3">
            {r.organization_avatar && (
              <img src={r.organization_avatar} alt="" className="w-8 h-8 rounded-full" />
            )}
            <div>
              <span className="font-medium text-gray-900">{r.organization_name}</span>
              <span className="ml-2 text-sm text-gray-500">{r.repo_name}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex flex-wrap gap-1">
              {r.matched_stack.map((tech) => (
                <span key={tech} className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs">
                  {tech}
                </span>
              ))}
            </div>
            <span className="text-sm font-semibold text-indigo-600">{r.match_score}%</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function SearchPage() {
  const queryClient = useQueryClient();
  const [activeSearchId, setActiveSearchId] = useState<string | null>(null);

  const { data: history } = useQuery({
    queryKey: ['searchHistory'],
    queryFn: api.getSearchHistory,
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

  return (
    <div className="space-y-6">
      <SetupChecklist />
      <SearchForm onSubmit={(config) => createSearch.mutate(config)} />

      {createSearch.isError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
          {createSearch.error.message}
        </div>
      )}

      {activeSearch && (
        <div className="space-y-4">
          <SearchStatus search={activeSearch} />
          {activeSearch.status === 'completed' && (
            <SearchResultsList searchId={activeSearch.id} />
          )}
        </div>
      )}

      {history?.results && history.results.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-gray-900">Search History</h3>
          {history.results.map((s: SearchQuery) => (
            <div
              key={s.id}
              onClick={() => setActiveSearchId(s.id)}
              className="cursor-pointer"
            >
              <SearchStatus search={s} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
