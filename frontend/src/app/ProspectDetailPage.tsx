import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { Repo, Contributor, Contact, JobListing } from '../types/api';
import TechChip, { groupByCategory } from '../components/TechChip';

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

  const { data: jobsData } = useQuery({
    queryKey: ['orgJobs', orgId],
    queryFn: () => api.getOrgJobs(orgId),
    enabled: !!orgId,
  });

  const saveProspect = useMutation({
    mutationFn: () => api.saveProspect(orgId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['savedProspects'] });
    },
  });

  const enrichOrg = useMutation({
    mutationFn: () => api.enrichOrg(orgId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contacts', orgId] }),
  });

  const checkJobs = useMutation({
    mutationFn: () => api.checkOrgJobs(orgId),
    onSuccess: (data) => {
      if (data.status === 'probing') {
        // Poll for results after a few seconds
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['orgJobs', orgId] });
        }, 5000);
      } else {
        queryClient.invalidateQueries({ queryKey: ['orgJobs', orgId] });
      }
    },
  });

  if (isLoading) return <p className="text-gray-500">Loading...</p>;
  if (!org) return <p className="text-gray-500">Company not found.</p>;

  const hasContacts = contacts && contacts.length > 0;
  const jobs: JobListing[] = jobsData?.results ?? [];
  const hasJobs = jobs.length > 0;

  // Aggregate tech stack across all repos, grouped by category
  const allDetections: Array<{ technology_name: string; category: string }> = [];
  org.repos?.forEach((repo: Repo) => {
    repo.stack_detections?.forEach((d) => allDetections.push(d));
  });
  const grouped = groupByCategory(allDetections);

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="text-sm text-indigo-600 hover:underline cursor-pointer">
        &larr; Back
      </button>

      {/* Company header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            {org.avatar_url && (
              <img src={org.avatar_url} alt="" className="w-16 h-16 rounded-full" />
            )}
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900">{org.name || org.github_login}</h1>
                {hasJobs && (
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                    Hiring
                  </span>
                )}
              </div>
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
              {(grouped.stack.length > 0 || grouped.aiTools.length > 0 || grouped.infra.length > 0) && (
                <div className="flex flex-wrap gap-1.5 items-center mt-3">
                  {grouped.stack.map((tech) => (
                    <TechChip key={tech} name={tech} category="backend" size="md" />
                  ))}
                  {grouped.aiTools.length > 0 && grouped.stack.length > 0 && (
                    <span className="text-gray-300 mx-0.5">|</span>
                  )}
                  {grouped.aiTools.map((tool) => (
                    <TechChip key={tool} name={tool} category="ai_tool" size="md" />
                  ))}
                  {grouped.infra.length > 0 && (grouped.stack.length > 0 || grouped.aiTools.length > 0) && (
                    <span className="text-gray-300 mx-0.5">|</span>
                  )}
                  {grouped.infra.map((item) => (
                    <TechChip key={item} name={item} category="infra" size="md" />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Action cards — what can you do with this company */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <button
          onClick={() => saveProspect.mutate()}
          disabled={saveProspect.isPending}
          className="bg-white rounded-lg shadow p-4 text-left hover:shadow-md transition-shadow cursor-pointer border-2 border-transparent hover:border-indigo-200"
        >
          <p className="font-medium text-gray-900 text-sm">
            {saveProspect.isSuccess ? 'Saved!' : saveProspect.isPending ? 'Saving...' : 'Save Company'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Add to your saved companies list for later.</p>
        </button>

        <button
          onClick={() => checkJobs.mutate()}
          disabled={checkJobs.isPending}
          className="bg-white rounded-lg shadow p-4 text-left hover:shadow-md transition-shadow cursor-pointer border-2 border-transparent hover:border-emerald-200"
        >
          <p className="font-medium text-gray-900 text-sm">
            {checkJobs.isPending ? 'Checking...' : hasJobs ? `${jobs.length} Open Roles` : 'Check Open Roles'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Search Greenhouse, Lever, Ashby, Workable for jobs.</p>
        </button>

        <button
          onClick={() => enrichOrg.mutate()}
          disabled={enrichOrg.isPending}
          className="bg-white rounded-lg shadow p-4 text-left hover:shadow-md transition-shadow cursor-pointer border-2 border-transparent hover:border-green-200"
        >
          <p className="font-medium text-gray-900 text-sm">
            {enrichOrg.isPending ? 'Finding contacts...' : 'Find Email Contacts'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Use Hunter.io to find engineering team emails.</p>
        </button>

        <button
          onClick={() => navigate(`/outreach?orgId=${orgId}`)}
          className="bg-white rounded-lg shadow p-4 text-left hover:shadow-md transition-shadow cursor-pointer border-2 border-transparent hover:border-purple-200"
        >
          <p className="font-medium text-gray-900 text-sm">Write Outreach Message</p>
          <p className="text-xs text-gray-500 mt-1">Generate a personalized cold email or LinkedIn message.</p>
        </button>
      </div>

      {enrichOrg.isError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
          {enrichOrg.error.message}
        </div>
      )}

      {/* Open Roles */}
      {hasJobs && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Open Roles</h2>
          <p className="text-xs text-gray-500 mb-4">
            Active job listings found on {jobs[0]?.ats_platform ? jobs[0].ats_platform.charAt(0).toUpperCase() + jobs[0].ats_platform.slice(1) : 'ATS'}. Click to apply.
          </p>
          <div className="space-y-2">
            {jobs.map((job: JobListing) => (
              <a
                key={job.id}
                href={job.apply_url}
                target="_blank"
                rel="noreferrer"
                className="block border border-gray-200 rounded-md p-3 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-sm text-gray-900">{job.title}</span>
                    {job.department && (
                      <span className="ml-2 text-xs text-gray-500">{job.department}</span>
                    )}
                  </div>
                  <span className="text-xs text-indigo-600 font-medium">Apply &rarr;</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  {job.location && (
                    <span className="text-xs text-gray-500">{job.location}</span>
                  )}
                  {job.employment_type && (
                    <span className="text-xs text-gray-400">{job.employment_type}</span>
                  )}
                </div>
                {job.detected_techs.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {job.detected_techs.map((tech) => (
                      <span key={tech} className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs">
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Repos */}
      {org.repos?.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Repositories</h2>
          <p className="text-xs text-gray-500 mb-4">What this company is building on GitHub.</p>
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
                <div className="flex flex-wrap gap-1 items-center mt-2">
                  {(() => {
                    const g = groupByCategory(repo.stack_detections || []);
                    return (
                      <>
                        {g.stack.map((tech) => (
                          <TechChip key={tech} name={tech} category="backend" />
                        ))}
                        {g.aiTools.length > 0 && g.stack.length > 0 && (
                          <span className="text-gray-300 mx-0.5">|</span>
                        )}
                        {g.aiTools.map((tool) => (
                          <TechChip key={tool} name={tool} category="ai_tool" />
                        ))}
                        {(repo.has_docker || repo.has_ci_cd || repo.has_tests) && (g.stack.length > 0 || g.aiTools.length > 0) && (
                          <span className="text-gray-300 mx-0.5">|</span>
                        )}
                        {repo.has_docker && <TechChip name="Docker" category="infra" />}
                        {repo.has_ci_cd && <TechChip name="CI/CD" category="infra" />}
                        {repo.has_tests && <TechChip name="Tests" category="infra" />}
                      </>
                    );
                  })()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contributors */}
      {org.top_contributors?.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Top Contributors</h2>
          <p className="text-xs text-gray-500 mb-4">People actively building at this company.</p>
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

      {/* Contacts */}
      {hasContacts ? (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Email Contacts</h2>
          <p className="text-xs text-gray-500 mb-4">Verified contacts from Hunter.io. Click an email to start a message.</p>
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
      ) : (
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-6 text-center">
          <p className="text-sm text-gray-600 mb-2">No contacts found yet.</p>
          <p className="text-xs text-gray-400">
            Click "Find Email Contacts" above to search for engineering team emails via Hunter.io.
            Requires a Hunter.io API key in Settings.
          </p>
        </div>
      )}
    </div>
  );
}
