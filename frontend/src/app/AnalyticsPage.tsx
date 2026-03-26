import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import SEO from '../components/SEO';

const API_BASE = '/api';

function fetchDashboard(days: number) {
  const token = localStorage.getItem('auth_token');
  return fetch(`${API_BASE}/analytics/dashboard/?days=${days}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  }).then((r) => {
    if (!r.ok) throw new Error('Failed to load analytics');
    return r.json();
  });
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg shadow p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">{title}</h3>
      {children}
    </div>
  );
}

function Bar({ label, count, max }: { label: string; count: number; max: number }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3 py-1">
      <span className="text-sm text-gray-700 w-40 truncate">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
        <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm font-medium text-gray-900 w-10 text-right">{count}</span>
    </div>
  );
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(7);

  const { data, isLoading, error } = useQuery({
    queryKey: ['analyticsDashboard', days],
    queryFn: () => fetchDashboard(days),
    refetchInterval: 60000,
  });

  return (
    <div className="space-y-6">
      <SEO title="Analytics" />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 text-sm mt-1">User behavior and traffic data</p>
        </div>
        <div className="flex gap-1">
          {[1, 7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium cursor-pointer ${
                days === d ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {d === 1 ? 'Today' : `${d}d`}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <p className="text-gray-500">Loading...</p>}
      {error && <p className="text-red-600 text-sm">Error: {(error as Error).message}</p>}

      {data && (
        <>
          {/* Top-level stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Stat label="Visitors" value={data.summary.human_sessions} />
            <Stat label="Page Views" value={data.summary.page_views} />
            <Stat label="Bounce Rate" value={`${data.behavior.bounce_rate}%`} />
            <Stat label="Avg Pages/Session" value={data.behavior.avg_pages_per_session} />
          </div>

          {/* User Behavior Events */}
          {data.events && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Stat label="Job Searches" value={data.job_metrics?.searches ?? 0} />
              <Stat label="Job Clicks" value={data.job_metrics?.job_clicks ?? 0} />
              <Stat label="Apply Clicks" value={data.job_metrics?.apply_clicks ?? 0} />
              <Stat label="Company Saves" value={data.search_metrics?.company_saves ?? 0} />
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Top Events */}
            {data.events?.top_events?.length > 0 && (
              <Section title="Top Events">
                {(() => {
                  const max = data.events.top_events[0]?.count ?? 1;
                  return data.events.top_events.slice(0, 10).map((e: { category: string; event_type: string; count: number }) => (
                    <Bar key={`${e.category}/${e.event_type}`} label={`${e.category}/${e.event_type}`} count={e.count} max={max} />
                  ));
                })()}
              </Section>
            )}

            {/* Top Searched Techs */}
            {data.top_searched_techs?.length > 0 && (
              <Section title="Top Searched Technologies">
                {(() => {
                  const max = data.top_searched_techs[0]?.count ?? 1;
                  return data.top_searched_techs.map((t: { tech: string; count: number }) => (
                    <Bar key={t.tech} label={t.tech} count={t.count} max={max} />
                  ));
                })()}
              </Section>
            )}

            {/* Top Pages */}
            <Section title="Top Pages">
              {(() => {
                const max = data.top_pages[0]?.views ?? 1;
                return data.top_pages.slice(0, 10).map((p: { path: string; views: number }) => (
                  <Bar key={p.path} label={p.path} count={p.views} max={max} />
                ));
              })()}
            </Section>

            {/* Referrers */}
            {data.referrers?.length > 0 && (
              <Section title="Traffic Sources">
                {(() => {
                  const max = data.referrers[0]?.count ?? 1;
                  return data.referrers.map((r: { referrer_domain: string; count: number }) => (
                    <Bar key={r.referrer_domain} label={r.referrer_domain} count={r.count} max={max} />
                  ));
                })()}
              </Section>
            )}

            {/* Devices */}
            <Section title="Devices">
              {data.devices.map((d: { device_type: string; count: number }) => (
                <Bar key={d.device_type} label={d.device_type} count={d.count} max={data.devices[0]?.count ?? 1} />
              ))}
            </Section>

            {/* Countries */}
            {data.countries?.length > 0 && (
              <Section title="Countries">
                {(() => {
                  const max = data.countries[0]?.count ?? 1;
                  return data.countries.map((c: { country: string; count: number }) => (
                    <Bar key={c.country} label={c.country} count={c.count} max={max} />
                  ));
                })()}
              </Section>
            )}

            {/* Auth Events */}
            <Section title="Auth Events">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Google success</span><span className="font-medium">{data.auth.google_success}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Google errors</span><span className="font-medium text-red-600">{data.auth.google_error}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">GitHub success</span><span className="font-medium">{data.auth.github_success}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">GitHub errors</span><span className="font-medium text-red-600">{data.auth.github_error}</span></div>
              </div>
            </Section>

            {/* Funnel */}
            <Section title="Conversion Funnel">
              {(() => {
                const steps = [
                  { label: 'Landed', value: data.funnel.landed },
                  { label: 'Visited Login', value: data.funnel.visited_login },
                  { label: 'Completed Auth', value: data.funnel.completed_auth },
                  { label: 'Reached Dashboard', value: data.funnel.reached_dashboard },
                  { label: 'Viewed Company', value: data.funnel.viewed_company },
                  { label: 'Visited Settings', value: data.funnel.visited_settings },
                ];
                const max = steps[0]?.value ?? 1;
                return steps.map((s) => <Bar key={s.label} label={s.label} count={s.value} max={max} />);
              })()}
            </Section>
          </div>

          {/* Daily Breakdown */}
          {data.daily?.length > 0 && (
            <Section title="Daily Sessions">
              {(() => {
                const max = Math.max(...data.daily.map((d: { sessions: number }) => d.sessions));
                return data.daily.map((d: { day: string; sessions: number }) => (
                  <Bar key={d.day} label={d.day} count={d.sessions} max={max} />
                ));
              })()}
            </Section>
          )}

          {/* Recent Events */}
          {data.events?.recent?.length > 0 && (
            <Section title="Recent Events">
              <div className="space-y-1 max-h-80 overflow-y-auto">
                {data.events.recent.map((e: { event_type: string; category: string; label: string; created_at: string }, i: number) => (
                  <div key={i} className="flex items-center gap-3 text-sm py-1 border-b border-gray-50">
                    <span className="text-xs text-gray-400 w-28 flex-shrink-0">
                      {new Date(e.created_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                    </span>
                    <span className="px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-medium">
                      {e.category}/{e.event_type}
                    </span>
                    {e.label && <span className="text-gray-600 truncate">{e.label}</span>}
                  </div>
                ))}
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}
