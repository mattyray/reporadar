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

  if (isLoading) return <p className="text-gray-500">Loading prospects...</p>;

  const prospects = data?.results ?? [];

  if (!prospects.length) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No prospects yet</h2>
        <p className="text-gray-500">Run a search to discover organizations.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">Prospects</h2>
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
    </div>
  );
}
