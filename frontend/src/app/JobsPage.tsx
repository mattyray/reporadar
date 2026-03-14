import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import type { JobListing, ResumeProfile } from '../types/api';
import TechChipSelector from '../components/TechChipSelector';

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

export default function JobsPage() {
  const navigate = useNavigate();
  const [selectedTechs, setSelectedTechs] = useState<string[]>([]);
  const [locationFilter, setLocationFilter] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [selectedDays, setSelectedDays] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [searchTriggered, setSearchTriggered] = useState(false);

  // Load resume profile to auto-populate chips
  const { data: resumeProfile } = useQuery({
    queryKey: ['resumeProfile'],
    queryFn: api.getResumeProfile,
    retry: false,
  });

  const [resumeApplied, setResumeApplied] = useState(false);
  useEffect(() => {
    if (resumeProfile && (resumeProfile as ResumeProfile).tech_stack?.length && !resumeApplied && selectedTechs.length === 0) {
      setSelectedTechs((resumeProfile as ResumeProfile).tech_stack.map((t: string) => t.toLowerCase()));
      setResumeApplied(true);
    }
  }, [resumeProfile, resumeApplied, selectedTechs.length]);

  const techsParam = selectedTechs.join(',');

  const { data: jobsData, isLoading, isFetching } = useQuery({
    queryKey: ['jobSearch', techsParam, locationFilter, selectedSource, selectedDays, remoteOnly],
    queryFn: () => api.searchJobs({
      techs: techsParam || undefined,
      location: locationFilter || undefined,
      days: selectedDays || undefined,
      source: selectedSource || undefined,
      remote: remoteOnly ? 'true' : undefined,
    }),
    enabled: searchTriggered,
  });

  const jobs: JobListing[] = jobsData?.results ?? [];
  const totalCount: number = jobsData?.count ?? jobs.length;

  const handleSearch = () => {
    setSearchTriggered(true);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Job Search</h1>
        <p className="text-gray-500 mt-1">
          Search open roles across ATS boards, RemoteOK, Remotive, We Work Remotely, and HN Who's Hiring.
        </p>
      </div>

      {/* Search controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <TechChipSelector
          selected={selectedTechs}
          onChange={setSelectedTechs}
          label="What technologies are you looking for?"
          hint="Click to select, or type your own below."
        />

        <div className="mt-4 pt-4 border-t border-gray-100">
          <label className="block text-sm font-medium text-gray-700 mb-1">Location (optional)</label>
          <input
            type="text"
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
            placeholder="e.g. Remote, San Francisco, London"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap items-center gap-4">
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
          <label className="flex items-center gap-2 cursor-pointer mt-5">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-sm font-medium text-gray-700">Remote only</span>
          </label>
        </div>

        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="mt-4 w-full bg-indigo-600 text-white rounded-md py-2.5 px-4 font-medium hover:bg-indigo-700 disabled:opacity-50 cursor-pointer"
        >
          {isFetching ? 'Searching...' : 'Search Jobs'}
        </button>
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
            {totalCount > jobs.length && ` (showing first ${jobs.length})`}
          </p>
          {jobs.map((job: JobListing) => (
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
                                return tl === thl || tl.includes(thl) || thl.includes(tl);
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
        </div>
      )}
    </div>
  );
}
