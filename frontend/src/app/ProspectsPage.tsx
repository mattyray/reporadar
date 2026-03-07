import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import type { Organization } from '../types/api';

export default function ProspectsPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ['prospects'],
    queryFn: api.getProspects,
  });

  if (isLoading) return <p className="text-gray-500">Loading...</p>;

  const prospects = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Companies</h2>
        <p className="text-sm text-gray-500 mt-1">
          Organizations discovered from your searches. Click any company to see their repos, tech stack, team, and contact info.
        </p>
      </div>

      {!prospects.length ? (
        <div className="text-center py-16 bg-white rounded-lg shadow">
          <div className="text-4xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No companies yet</h3>
          <p className="text-gray-500 mb-6 max-w-md mx-auto">
            Run a search from the Dashboard to discover GitHub organizations that match your tech stack.
            Companies will show up here as they're found.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-indigo-600 text-white px-6 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 cursor-pointer"
          >
            Go to Dashboard
          </button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {prospects.map((org: Organization) => (
            <div
              key={org.id}
              onClick={() => navigate(`/prospects/${org.id}`)}
              className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-3 mb-3">
                {org.avatar_url && (
                  <img src={org.avatar_url} alt="" className="w-10 h-10 rounded-full" />
                )}
                <div>
                  <h3 className="font-medium text-gray-900">{org.name || org.github_login}</h3>
                  {org.location && (
                    <p className="text-xs text-gray-500">{org.location}</p>
                  )}
                </div>
              </div>
              {org.description && (
                <p className="text-sm text-gray-600 line-clamp-2">{org.description}</p>
              )}
              <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                <span>{org.public_repos_count} repos</span>
                {org.website && <span>| {org.website}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
