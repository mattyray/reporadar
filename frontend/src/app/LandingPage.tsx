import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import SEO from '../components/SEO';

function useStats() {
  const [stats, setStats] = useState<{ active_jobs: number; companies: number; tech_count: number } | null>(null);
  useEffect(() => {
    fetch('/api/analytics/stats/')
      .then(r => r.ok ? r.json() : null)
      .then(data => data && setStats(data))
      .catch(() => {});
  }, []);
  return stats;
}

export default function LandingPage() {
  const stats = useStats();

  return (
    <div className="min-h-screen bg-white">
      <SEO />
      {/* Nav */}
      <nav className="border-b border-gray-200 px-6 py-4 flex items-center justify-between max-w-6xl mx-auto">
        <span className="text-xl font-bold text-gray-900">RepoRadar</span>
        <Link
          to="/login"
          className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800"
        >
          Sign in
        </Link>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
          Find jobs at companies that use{' '}
          <span className="text-blue-600">your tech stack</span>
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          Upload your resume and instantly see matching jobs from thousands of companies.
          RepoRadar combines job boards, ATS feeds, and GitHub analysis to surface
          roles that match your skills — not just keywords.
        </p>
        <Link
          to="/jobs"
          className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700"
        >
          Try it now — no signup needed
        </Link>

        {stats && (stats.active_jobs > 0 || stats.companies > 0) && (
          <div className="mt-10 flex items-center justify-center gap-8 text-sm text-gray-500">
            {stats.active_jobs > 0 && (
              <div>
                <span className="text-2xl font-bold text-gray-900">{stats.active_jobs.toLocaleString()}</span>
                <span className="ml-1">active jobs</span>
              </div>
            )}
            {stats.companies > 0 && (
              <div>
                <span className="text-2xl font-bold text-gray-900">{stats.companies.toLocaleString()}</span>
                <span className="ml-1">companies</span>
              </div>
            )}
            {stats.tech_count > 0 && (
              <div>
                <span className="text-2xl font-bold text-gray-900">{stats.tech_count.toLocaleString()}</span>
                <span className="ml-1">technologies tracked</span>
              </div>
            )}
          </div>
        )}
      </section>

      {/* How it works */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            How it works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Step
              number="1"
              title="Upload your resume"
              description="Drop in your PDF or DOCX. AI extracts your tech stack, key projects, and experience — no forms to fill out."
            />
            <Step
              number="2"
              title="See matching jobs"
              description="We match your skills against thousands of jobs from ATS boards, RemoteOK, Remotive, We Work Remotely, and HN Who's Hiring."
            />
            <Step
              number="3"
              title="Apply directly"
              description="Click through to apply on the company's job board. Each listing shows matched technologies so you know exactly why it's a fit."
            />
          </div>
        </div>
      </section>

      {/* What we detect */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            What we detect
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <DetectCard
              title="Tech Stack"
              items={['requirements.txt', 'package.json', 'go.mod', 'Cargo.toml', 'Gemfile', 'pom.xml']}
              description="We parse dependency files across Python, JS, Go, Rust, Ruby, and Java ecosystems."
            />
            <DetectCard
              title="AI Tool Signals"
              items={['CLAUDE.md', '.cursor/', 'copilot-instructions.md', '.windsurfrules']}
              description="Find companies using Claude Code, Cursor, GitHub Copilot, and Windsurf."
            />
            <DetectCard
              title="Production Signals"
              items={['Dockerfile', '.github/workflows/', 'pytest.ini', 'Procfile']}
              description="Docker, CI/CD, test suites, and deployment configs signal mature engineering."
            />
            <DetectCard
              title="Team & Activity"
              items={['Contributors', 'Recent pushes', 'Stars & forks', 'Org size']}
              description="Active teams with multiple contributors score higher than abandoned repos."
            />
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Completely free</h2>
          <p className="text-gray-600 mb-12">No credit card, no API keys, no catch.</p>
          <div className="max-w-sm mx-auto">
            <div className="bg-white rounded-xl p-8 shadow-sm border-2 border-blue-600 text-left">
              <h3 className="text-lg font-semibold text-blue-600 mb-2">Free</h3>
              <p className="text-3xl font-bold text-gray-900 mb-6">$0</p>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li className="flex items-start gap-2"><span className="text-green-600 mt-0.5">&#10003;</span> AI resume parsing</li>
                <li className="flex items-start gap-2"><span className="text-green-600 mt-0.5">&#10003;</span> Job matching across 5+ sources</li>
                <li className="flex items-start gap-2"><span className="text-green-600 mt-0.5">&#10003;</span> GitHub company search</li>
                <li className="flex items-start gap-2"><span className="text-green-600 mt-0.5">&#10003;</span> Tech stack detection & scoring</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8 text-center text-sm text-gray-500">
        <p>Built by <a href="https://github.com/mattyray" className="text-gray-700 hover:underline" target="_blank" rel="noopener noreferrer">Matt Raynor</a> with Django, React, and Claude.</p>
      </footer>
    </div>
  );
}

function Step({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="text-center">
      <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-lg font-bold">
        {number}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  );
}

function DetectCard({ title, items, description }: { title: string; items: string[]; description: string }) {
  return (
    <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm mb-3">{description}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="bg-white border border-gray-300 rounded-md px-2 py-1 text-xs font-mono text-gray-700">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
