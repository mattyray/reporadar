import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { Repo, Contributor, Contact } from '../types/api';

export default function ProspectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const orgId = Number(id);

  const { data: org, isLoading } = useQuery({
    queryKey: ['prospect', orgId],
    queryFn: () => api.getProspect(orgId),
    enabled: !!orgId,
  });

  const { data: contacts } = useQuery({
    queryKey: ['contacts', orgId],
    queryFn: () => api.getContacts(orgId),
    enabled: !!orgId,
  });

  const saveProspect = useMutation({
    mutationFn: () => api.saveProspect(orgId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['savedProspects'] }),
  });

  const enrichOrg = useMutation({
    mutationFn: () => api.enrichOrg(orgId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contacts', orgId] }),
  });

  if (isLoading) return <p className="text-gray-500">Loading...</p>;
  if (!org) return <p className="text-gray-500">Prospect not found.</p>;

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="text-sm text-indigo-600 hover:underline cursor-pointer">
        Back
      </button>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {org.avatar_url && (
              <img src={org.avatar_url} alt="" className="w-16 h-16 rounded-full" />
            )}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{org.name || org.github_login}</h1>
              {org.description && <p className="text-gray-600 mt-1">{org.description}</p>}
              <div className="flex gap-3 mt-2 text-sm text-gray-500">
                {org.location && <span>{org.location}</span>}
                {org.website && (
                  <a href={org.website} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
                    {org.website}
                  </a>
                )}
                <a href={org.github_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
                  GitHub
                </a>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => saveProspect.mutate()}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 cursor-pointer"
            >
              Save
            </button>
            <button
              onClick={() => enrichOrg.mutate()}
              className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 cursor-pointer"
            >
              {enrichOrg.isPending ? 'Enriching...' : 'Enrich Contacts'}
            </button>
            <button
              onClick={() => navigate(`/outreach?orgId=${orgId}`)}
              className="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 cursor-pointer"
            >
              Generate Outreach
            </button>
          </div>
        </div>
      </div>

      {org.repos?.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Repositories</h2>
          <div className="space-y-3">
            {org.repos.map((repo: Repo) => (
              <div key={repo.id} className="border border-gray-200 rounded-md p-3">
                <div className="flex items-center justify-between">
                  <a href={repo.url} target="_blank" rel="noreferrer" className="font-medium text-indigo-600 hover:underline">
                    {repo.name}
                  </a>
                  <div className="flex gap-2 text-xs text-gray-500">
                    <span>{repo.stars} stars</span>
                    <span>{repo.forks} forks</span>
                  </div>
                </div>
                {repo.description && (
                  <p className="text-sm text-gray-600 mt-1">{repo.description}</p>
                )}
                <div className="flex flex-wrap gap-1 mt-2">
                  {repo.stack_detections?.map((d) => (
                    <span key={d.technology_name} className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs">
                      {d.technology_name}
                    </span>
                  ))}
                  {repo.has_claude_md && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">Claude</span>}
                  {repo.has_cursor_config && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">Cursor</span>}
                  {repo.has_docker && <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">Docker</span>}
                  {repo.has_ci_cd && <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">CI/CD</span>}
                  {repo.has_tests && <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">Tests</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {org.top_contributors?.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Contributors</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {org.top_contributors.map((c: Contributor) => (
              <div key={c.github_username} className="flex items-center gap-3 border border-gray-200 rounded-md p-3">
                {c.avatar_url && <img src={c.avatar_url} alt="" className="w-8 h-8 rounded-full" />}
                <div>
                  <a href={c.profile_url} target="_blank" rel="noreferrer" className="font-medium text-sm text-indigo-600 hover:underline">
                    {c.name || c.github_username}
                  </a>
                  {c.company && <p className="text-xs text-gray-500">{c.company}</p>}
                  <p className="text-xs text-gray-400">{c.contributions} contributions</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {contacts && contacts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Contacts</h2>
          <div className="space-y-2">
            {contacts.map((c: Contact) => (
              <div key={c.id} className="flex items-center justify-between border border-gray-200 rounded-md p-3">
                <div>
                  <span className="font-medium text-sm text-gray-900">
                    {c.first_name} {c.last_name}
                  </span>
                  {c.position && <span className="ml-2 text-sm text-gray-500">{c.position}</span>}
                  {c.is_engineering_lead && (
                    <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">Eng Lead</span>
                  )}
                </div>
                <div className="text-sm">
                  {c.email && (
                    <a href={`mailto:${c.email}`} className="text-indigo-600 hover:underline">
                      {c.email}
                    </a>
                  )}
                  {c.linkedin_url && (
                    <a href={c.linkedin_url} target="_blank" rel="noreferrer" className="ml-3 text-indigo-600 hover:underline">
                      LinkedIn
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
