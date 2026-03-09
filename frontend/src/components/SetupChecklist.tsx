import { useAuth } from '../hooks/useAuth';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

export default function SetupChecklist() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data: resumeProfile } = useQuery({
    queryKey: ['resumeProfile'],
    queryFn: api.getResumeProfile,
    retry: false,
  });

  if (!user) return null;

  const githubMissing = !user.github_connected;
  const resumeMissing = !resumeProfile;
  const hunterMissing = !user.has_hunter_key;

  // Nothing left to set up
  if (!githubMissing && !resumeMissing && !hunterMissing) return null;

  // GitHub is the #1 priority — show a big, impossible-to-miss banner
  if (githubMissing) {
    return (
      <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-amber-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-amber-900">Connect GitHub to start searching</h3>
            <p className="text-sm text-amber-700 mt-1">
              RepoRadar needs your GitHub account to search 28M+ repositories and find companies using your tech stack. Without it, you'll only see demo results.
            </p>
            <a
              href={`https://reporadar-production.up.railway.app/api/auth/github/start/?token=${localStorage.getItem('auth_token') || ''}`}
              className="inline-flex items-center gap-2 mt-4 bg-gray-900 text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-gray-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              Connect GitHub
            </a>
          </div>
        </div>

        {/* Secondary items shown smaller underneath */}
        {(resumeMissing || hunterMissing) && (
          <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-amber-200">
            <span className="text-xs text-amber-600 font-medium">Also recommended:</span>
            {resumeMissing && (
              <span className="text-xs text-amber-700 bg-amber-100 px-2.5 py-1 rounded-full">Upload resume for auto-detect</span>
            )}
            {hunterMissing && (
              <button
                onClick={() => navigate('/settings')}
                className="text-xs text-amber-700 bg-amber-100 px-2.5 py-1 rounded-full hover:bg-amber-200 cursor-pointer"
              >
                Add Hunter.io key for emails
              </button>
            )}
          </div>
        )}
      </div>
    );
  }

  // GitHub is connected — show smaller hints for remaining items
  const remaining: { label: string; onClick?: () => void }[] = [];
  if (resumeMissing) remaining.push({ label: 'Upload resume for auto-detect' });
  if (hunterMissing) remaining.push({ label: 'Add Hunter.io key for emails', onClick: () => navigate('/settings') });

  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
      <span className="font-medium text-gray-700">Unlock more:</span>
      {remaining.map((item) => (
        item.onClick ? (
          <button
            key={item.label}
            onClick={item.onClick}
            className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 cursor-pointer"
          >
            {item.label}
          </button>
        ) : (
          <span key={item.label} className="px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full">
            {item.label}
          </span>
        )
      ))}
    </div>
  );
}
