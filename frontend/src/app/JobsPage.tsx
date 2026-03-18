import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../lib/api';
import type { JobListing, ResumeProfile } from '../types/api';
import SEO from '../components/SEO';
import { useAuth } from '../hooks/useAuth';
import TechChipSelector from '../components/TechChipSelector';
import ResumeUploadBanner from '../components/ResumeUploadBanner';
import SetupChecklist from '../components/SetupChecklist';

const ANON_VISIBLE_COUNT = 5;

const SOURCE_TABS = [
  { key: '', label: 'All Sources' },
  { key: 'ats', label: 'ATS Boards' },
  { key: 'remoteok', label: 'RemoteOK' },
  { key: 'remotive', label: 'Remotive' },
  { key: 'wwr', label: 'We Work Remotely' },
  { key: 'hn', label: 'HN Hiring' },
] as const;

const RECENCY_OPTIONS = [
  { value: '', label: 'Any time' },
  { value: '1', label: 'Last 24 hours' },
  { value: '3', label: 'Last 3 days' },
  { value: '7', label: 'This week' },
  { value: '30', label: 'This month' },
] as const;

const SOURCE_LABELS: Record<string, string> = {
  ats: 'ATS Board',
  remoteok: 'RemoteOK',
  remotive: 'Remotive',
  wwr: 'We Work Remotely',
  hn: 'HN Who\'s Hiring',
};

const SOURCE_URLS: Record<string, string> = {
  remoteok: 'https://remoteok.com',
  remotive: 'https://remotive.com',
  wwr: 'https://weworkremotely.com',
  hn: 'https://news.ycombinator.com',
};

const REMOTE_REGION_OPTIONS = [
  { value: 'us_only,us_canada,americas,global,unspecified', label: 'US-friendly (US, Americas, Global, Unspecified)' },
  { value: 'us_only', label: 'US Only' },
  { value: 'us_only,us_canada', label: 'US & Canada' },
  { value: 'europe,emea,global,unspecified', label: 'Europe-friendly' },
  { value: 'global', label: 'Global / Worldwide only' },
  { value: '', label: 'Any region' },
] as const;

export default function JobsPage() {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [selectedTechs, setSelectedTechs] = useState<string[]>([]);
  const [locationFilter, setLocationFilter] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [selectedDays, setSelectedDays] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [includeHybrid, setIncludeHybrid] = useState(false);
  const [remoteRegion, setRemoteRegion] = useState('us_only,us_canada,americas,global,unspecified');
  const [searchTriggered, setSearchTriggered] = useState(false);

  // Load resume profile to auto-populate chips
  const { data: resumeProfile } = useQuery({
    queryKey: ['resumeProfile'],
    queryFn: api.getResumeProfile,
    retry: false,
    enabled: isAuthenticated,
  });

  const hasResume = !!(resumeProfile && (resumeProfile as ResumeProfile).parsed_at);

  // Auto-populate chips from resume and auto-trigger search
  const [resumeApplied, setResumeApplied] = useState(false);
  useEffect(() => {
    if (resumeProfile && (resumeProfile as ResumeProfile).tech_stack?.length && !resumeApplied && selectedTechs.length === 0) {
      setSelectedTechs((resumeProfile as ResumeProfile).tech_stack.map((t: string) => t.toLowerCase()));
      setResumeApplied(true);
      setSearchTriggered(true);
    }
  }, [resumeProfile, resumeApplied, selectedTechs.length]);

  const handleResumeParsed = (techStack: string[]) => {
    setSelectedTechs(techStack);
    setResumeApplied(true);
    setSearchTriggered(true);
  };

  const techsParam = selectedTechs.join(',');

  // Build workplace_type filter
  const workplaceTypeParam = remoteOnly
    ? (includeHybrid ? 'remote,hybrid' : 'remote')
    : undefined;

  const { data: jobsData, isLoading, isFetching } = useQuery({
    queryKey: ['jobSearch', techsParam, locationFilter, selectedSource, selectedDays, remoteOnly, includeHybrid, remoteRegion],
    queryFn: () => api.searchJobs({
      techs: techsParam || undefined,
      location: locationFilter || undefined,
      days: selectedDays || undefined,
      source: selectedSource || undefined,
      remote: remoteOnly ? 'true' : undefined,
      remote_region: (remoteOnly && remoteRegion) ? remoteRegion : undefined,
      workplace_type: workplaceTypeParam,
    }),
    enabled: searchTriggered,
  });

  const jobs: JobListing[] = jobsData?.results ?? [];
  const totalCount: number = jobsData?.count ?? jobs.length;
  const visibleJobs = isAuthenticated ? jobs : jobs.slice(0, ANON_VISIBLE_COUNT);
  const hiddenJobs = !isAuthenticated ? jobs.slice(ANON_VISIBLE_COUNT, ANON_VISIBLE_COUNT + 3) : [];
  const hasHiddenJobs = !isAuthenticated && totalCount > ANON_VISIBLE_COUNT;

  const handleSearch = () => {
    setSearchTriggered(true);
  };

  return (
    <div className="space-y-6">
      <SEO title="Jobs" description="Browse matching job listings from companies that use your tech stack." />
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {user?.first_name ? `Welcome, ${user.first_name}` : 'Find Jobs'}
        </h1>
        <p className="text-gray-500 mt-1">
          {isAuthenticated
            ? "Upload your resume and we'll match you with open roles across thousands of companies."
            : 'Search thousands of tech jobs. Sign up to unlock all results and resume matching.'}
        </p>
      </div>

      {isAuthenticated && <SetupChecklist />}

      {/* Resume upload — the first thing new users see */}
      {isAuthenticated && <ResumeUploadBanner onParsed={handleResumeParsed} hasExisting={hasResume} />}

      {/* Resume applied indicator */}
      {hasResume && selectedTechs.length > 0 && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-2.5">
          <span className="font-medium">Auto-detected from your resume.</span>
          <span className="text-green-600">Adjust technologies below to refine your results.</span>
        </div>
      )}

      {/* Search controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <TechChipSelector
          selected={selectedTechs}
          onChange={setSelectedTechs}
          label="What technologies are you looking for?"
          hint="Click to select, or type your own below."
        />

        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex flex-wrap items-start gap-4">
            {/* Remote toggle */}
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={remoteOnly}
                  onChange={(e) => setRemoteOnly(e.target.checked)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm font-medium text-gray-700">Remote only</span>
              </label>
              {remoteOnly && (
                <label className="flex items-center gap-2 cursor-pointer mt-2 ml-6">
                  <input
                    type="checkbox"
                    checked={includeHybrid}
                    onChange={(e) => setIncludeHybrid(e.target.checked)}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-xs text-gray-500">Include hybrid</span>
                </label>
              )}
            </div>

            {/* Remote region dropdown — only shows when remote is checked */}
            {remoteOnly && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
                <select
                  value={remoteRegion}
                  onChange={(e) => setRemoteRegion(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  {REMOTE_REGION_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Posted within */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Posted within</label>
              <select
                value={selectedDays}
                onChange={(e) => setSelectedDays(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                {RECENCY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Location text search (for city/keyword when NOT doing remote filter) */}
          {!remoteOnly && (
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">Location (city, state, or keyword)</label>
              <input
                type="text"
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                placeholder="e.g. San Francisco, Austin TX, London"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>
          )}
        </div>

        <div className="mt-4 flex gap-2">
          <button
            onClick={handleSearch}
            disabled={isLoading}
            className="flex-1 bg-indigo-600 text-white rounded-md py-2.5 px-4 font-medium hover:bg-indigo-700 disabled:opacity-50 cursor-pointer"
          >
            {isFetching ? 'Searching...' : 'Search Jobs'}
          </button>
          <button
            onClick={() => {
              setSelectedTechs([]);
              setLocationFilter('');
              setSelectedSource('');
              setSelectedDays('');
              setRemoteOnly(false);
              setIncludeHybrid(false);
              setRemoteRegion('us_only,us_canada,americas,global,unspecified');
              setSearchTriggered(false);
              setResumeApplied(true);  // prevent resume techs from re-populating
            }}
            className="px-4 py-2.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 cursor-pointer"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Source tabs */}
      {searchTriggered && (
        <div className="flex flex-wrap gap-1 bg-white rounded-lg shadow px-3 py-2">
          {SOURCE_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setSelectedSource(tab.key)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium cursor-pointer transition-colors ${
                selectedSource === tab.key
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Results */}
      {searchTriggered && !isLoading && jobs.length === 0 && (
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-6 text-center">
          <p className="text-sm text-gray-600 mb-2">No jobs found matching your criteria.</p>
          <p className="text-xs text-gray-400">
            Try broadening your search or selecting a different source.
          </p>
        </div>
      )}

      {jobs.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-gray-500">
            {totalCount} job{totalCount !== 1 ? 's' : ''} found
            {isAuthenticated && totalCount > jobs.length && ` (showing first ${jobs.length})`}
          </p>
          {visibleJobs.map((job: JobListing) => (
            <div
              key={`${job.source}-${job.id}`}
              className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  {job.avatar_url ? (
                    <img src={job.avatar_url} alt="" className="w-10 h-10 rounded-full flex-shrink-0 mt-0.5" />
                  ) : (
                    <div className="w-10 h-10 rounded-full flex-shrink-0 mt-0.5 bg-gray-200 flex items-center justify-center">
                      <span className="text-gray-500 text-sm font-medium">
                        {(job.company_name || '?')[0].toUpperCase()}
                      </span>
                    </div>
                  )}
                  <div className="min-w-0">
                    <a
                      href={job.apply_url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-gray-900 hover:text-indigo-600"
                    >
                      {job.title}
                    </a>
                    <div className="flex items-center gap-2 mt-0.5">
                      {job.organization_id ? (
                        <button
                          onClick={() => navigate(`/prospects/${job.organization_id}`)}
                          className="text-sm text-indigo-600 hover:underline cursor-pointer"
                        >
                          {job.company_name}
                        </button>
                      ) : (
                        <span className="text-sm text-gray-600">{job.company_name}</span>
                      )}
                      {job.department && (
                        <span className="text-xs text-gray-400">{job.department}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {job.is_remote && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
                          {job.workplace_type === 'hybrid' ? 'Hybrid' : 'Remote'}
                        </span>
                      )}
                      {job.location && (
                        <span className="text-xs text-gray-500">{job.location}</span>
                      )}
                      {job.employment_type && (
                        <span className="text-xs text-gray-400">{job.employment_type}</span>
                      )}
                      {job.salary && (
                        <span className="text-xs text-green-600 font-medium">{job.salary}</span>
                      )}
                      {/* Source attribution */}
                      {job.source && job.source !== 'ats' ? (
                        <a
                          href={SOURCE_URLS[job.source] || '#'}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-gray-400 hover:text-gray-600"
                        >
                          via {SOURCE_LABELS[job.source] || job.source}
                        </a>
                      ) : job.ats_platform ? (
                        <span className="text-xs text-gray-300">
                          via {job.ats_platform.charAt(0).toUpperCase() + job.ats_platform.slice(1)}
                        </span>
                      ) : null}
                    </div>
                    {job.detected_techs.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {job.detected_techs.map((tech) => (
                          <span
                            key={tech}
                            className={`px-2 py-0.5 rounded text-xs ${
                              selectedTechs.some(t => {
                                const tl = t.toLowerCase();
                                const thl = tech.toLowerCase();
                                if (tl === thl) return true;
                                const re = new RegExp(`\\b${thl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`);
                                return re.test(tl);
                              })
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <a
                  href={job.apply_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-shrink-0 bg-indigo-600 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-indigo-700"
                >
                  Apply
                </a>
              </div>
            </div>
          ))}

          {/* Blurred cards + signup CTA for anonymous users */}
          {hasHiddenJobs && (
            <div className="relative">
              <div className="space-y-2 blur-sm pointer-events-none select-none" aria-hidden="true">
                {hiddenJobs.map((job: JobListing) => (
                  <div key={`blur-${job.source}-${job.id}`} className="bg-white rounded-lg shadow p-4">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-full bg-gray-200 flex-shrink-0" />
                      <div className="min-w-0">
                        <div className="font-medium text-gray-900">{job.title}</div>
                        <div className="text-sm text-gray-600">{job.company_name}</div>
                        {job.location && <div className="text-xs text-gray-500 mt-1">{job.location}</div>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/70 to-white flex flex-col items-center justify-center">
                <p className="text-lg font-semibold text-gray-900 mb-2">
                  {totalCount - ANON_VISIBLE_COUNT} more job{totalCount - ANON_VISIBLE_COUNT !== 1 ? 's' : ''} match your search
                </p>
                <Link
                  to="/login"
                  className="bg-indigo-600 text-white px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700"
                >
                  Sign up free to see all results
                </Link>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
