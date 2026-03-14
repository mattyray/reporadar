import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { Repo, Contributor, JobListing, RepoAnalysis } from '../types/api';
import TechChip, { groupByCategory } from '../components/TechChip';

function AnalysisButton({ repo }: { repo: Repo }) {
  const queryClient = useQueryClient();

  const analyze = useMutation({
    mutationFn: () => api.analyzeRepo(repo.id),
    onSuccess: () => {
      // Poll for results — analysis takes 10-30 seconds
      const poll = setInterval(() => {
        api.getRepoAnalysis(repo.id).then((updated) => {
          if (updated.ai_analysis_status === 'completed' || updated.ai_analysis_status === 'failed') {
            clearInterval(poll);
            queryClient.invalidateQueries({ queryKey: ['prospect'] });
          }
        });
      }, 3000);
    },
  });

  const status = repo.ai_analysis_status;
  const isWorking = status === 'pending' || status === 'analyzing' || analyze.isPending;

  if (status === 'completed') return null;

  return (
    <button
      onClick={() => analyze.mutate()}
      disabled={isWorking}
      className="mt-2 text-xs px-3 py-1.5 bg-violet-50 text-violet-700 border border-violet-200 rounded-md hover:bg-violet-100 transition-colors disabled:opacity-50 cursor-pointer"
    >
      {isWorking ? (
        <span className="flex items-center gap-1.5">
          <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Analyzing with AI — takes 30-60 seconds...
        </span>
      ) : status === 'failed' ? (
        'Retry AI Analysis'
      ) : (
        'Analyze with AI'
      )}
    </button>
  );
}

function QualityBadge({ label, value }: { label: string; value: boolean }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs ${value ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
      {value ? '\u2713' : '\u2717'} {label}
    </span>
  );
}

function AnalysisDisplay({ analysis }: { analysis: RepoAnalysis }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="mt-3 border-t border-violet-100 pt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs font-medium text-violet-700 hover:text-violet-900 cursor-pointer"
      >
        <span>{expanded ? '\u25BC' : '\u25B6'}</span>
        AI Analysis
      </button>

      {expanded && (
        <div className="mt-3 space-y-4 text-sm">
          {/* Summary */}
          <div>
            <p className="text-gray-700 leading-relaxed">{analysis.summary}</p>
          </div>

          {/* Tech Stack Breakdown */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Tech Stack</h4>
            <div className="grid grid-cols-2 gap-2">
              {analysis.tech_stack.languages?.length > 0 && (
                <div>
                  <span className="text-xs text-gray-400">Languages:</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {analysis.tech_stack.languages.map(l => (
                      <span key={l} className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">{l}</span>
                    ))}
                  </div>
                </div>
              )}
              {analysis.tech_stack.frameworks?.length > 0 && (
                <div>
                  <span className="text-xs text-gray-400">Frameworks:</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {analysis.tech_stack.frameworks.map(f => (
                      <span key={f} className="px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs">{f}</span>
                    ))}
                  </div>
                </div>
              )}
              {analysis.tech_stack.databases?.length > 0 && (
                <div>
                  <span className="text-xs text-gray-400">Databases:</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {analysis.tech_stack.databases.map(d => (
                      <span key={d} className="px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded text-xs">{d}</span>
                    ))}
                  </div>
                </div>
              )}
              {analysis.tech_stack.notable_libraries?.length > 0 && (
                <div>
                  <span className="text-xs text-gray-400">Libraries:</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {analysis.tech_stack.notable_libraries.map(l => (
                      <span key={l} className="px-1.5 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">{l}</span>
                    ))}
                  </div>
                </div>
              )}
              {analysis.tech_stack.ai_tools?.length > 0 && (
                <div>
                  <span className="text-xs text-gray-400">AI Tools:</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {analysis.tech_stack.ai_tools.map(t => (
                      <span key={t} className="px-1.5 py-0.5 bg-violet-50 text-violet-700 rounded text-xs">{t}</span>
                    ))}
                  </div>
                </div>
              )}
              {analysis.tech_stack.infrastructure?.length > 0 && (
                <div>
                  <span className="text-xs text-gray-400">Infrastructure:</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {analysis.tech_stack.infrastructure.map(i => (
                      <span key={i} className="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded text-xs">{i}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Architecture */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Architecture</h4>
            <p className="text-xs font-medium text-gray-800">{analysis.architecture.pattern}</p>
            <p className="text-xs text-gray-600 mt-0.5">{analysis.architecture.description}</p>
            {analysis.architecture.key_directories?.length > 0 && (
              <div className="mt-2 grid grid-cols-2 gap-1">
                {analysis.architecture.key_directories.map(d => (
                  <div key={d.path} className="text-xs">
                    <code className="text-violet-600 bg-violet-50 px-1 rounded">{d.path}</code>
                    <span className="text-gray-500 ml-1">{d.purpose}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Code Quality */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Code Quality</h4>
            <div className="flex flex-wrap gap-1.5">
              <QualityBadge label="Tests" value={analysis.code_quality.has_tests} />
              <QualityBadge label="CI/CD" value={analysis.code_quality.has_ci_cd} />
              <QualityBadge label="Linting" value={analysis.code_quality.has_linting} />
              <QualityBadge label="Types" value={analysis.code_quality.has_type_checking} />
              <QualityBadge label="Docs" value={analysis.code_quality.has_documentation} />
            </div>
            {analysis.code_quality.quality_notes && (
              <p className="text-xs text-gray-500 mt-1">{analysis.code_quality.quality_notes}</p>
            )}
          </div>

          {/* Maturity */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Project Maturity</h4>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded font-medium">{analysis.maturity.stage}</span>
              <span className="text-gray-500">{analysis.maturity.team_size_estimate}</span>
              <span className="text-gray-500">{analysis.maturity.activity_assessment}</span>
            </div>
            {analysis.maturity.signals?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {analysis.maturity.signals.map(s => (
                  <span key={s} className="text-xs text-gray-500">{s}</span>
                ))}
              </div>
            )}
          </div>

          {/* What they're building */}
          {analysis.what_they_are_building && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">What They're Building</h4>
              <p className="text-xs text-gray-700">{analysis.what_they_are_building}</p>
            </div>
          )}

          {/* Notable Patterns */}
          {analysis.notable_patterns?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Notable Patterns</h4>
              <ul className="text-xs text-gray-600 space-y-0.5">
                {analysis.notable_patterns.map(p => (
                  <li key={p} className="flex items-start gap-1">
                    <span className="text-violet-400 mt-0.5">&bull;</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Job Seeker Insights */}
          <div className="bg-gradient-to-r from-violet-50 to-indigo-50 rounded-md p-3">
            <h4 className="text-xs font-semibold text-violet-700 uppercase tracking-wider mb-1">Why Work Here</h4>
            <p className="text-xs text-gray-700">{analysis.interesting_for_job_seekers.why_work_here}</p>
            {analysis.interesting_for_job_seekers.tech_culture_signals?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {analysis.interesting_for_job_seekers.tech_culture_signals.map(s => (
                  <span key={s} className="px-1.5 py-0.5 bg-white/70 text-violet-700 rounded text-xs">{s}</span>
                ))}
              </div>
            )}
            {analysis.interesting_for_job_seekers.potential_roles?.length > 0 && (
              <div className="mt-1.5">
                <span className="text-xs text-gray-500">Potential roles: </span>
                <span className="text-xs text-gray-700">{analysis.interesting_for_job_seekers.potential_roles.join(', ')}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

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

      {/* Action cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
      </div>

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

                {/* AI Analysis — button or results */}
                {repo.ai_analysis_status === 'completed' && repo.ai_analysis ? (
                  <AnalysisDisplay analysis={repo.ai_analysis} />
                ) : (
                  <AnalysisButton repo={repo} />
                )}
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

    </div>
  );
}
