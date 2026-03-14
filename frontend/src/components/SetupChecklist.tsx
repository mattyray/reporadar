import { useAuth } from '../hooks/useAuth';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export default function SetupChecklist() {
  const { user } = useAuth();
  const { data: resumeProfile } = useQuery({
    queryKey: ['resumeProfile'],
    queryFn: api.getResumeProfile,
    retry: false,
  });

  if (!user) return null;

  const resumeMissing = !resumeProfile;
  const githubMissing = !user.github_connected;

  // Nothing left to set up
  if (!resumeMissing && !githubMissing) return null;

  // Resume is the #1 priority — show a prominent banner
  if (resumeMissing) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-base font-semibold text-blue-900">Upload your resume to get started</h3>
            <p className="text-sm text-blue-700 mt-1">
              We'll extract your tech stack and automatically find matching jobs across thousands of companies.
            </p>
          </div>
        </div>
        {githubMissing && (
          <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-blue-200">
            <span className="text-xs text-blue-600 font-medium">Also available:</span>
            <a
              href={`https://reporadar-production.up.railway.app/api/auth/github/start/?token=${localStorage.getItem('auth_token') || ''}`}
              className="text-xs text-blue-700 bg-blue-100 px-2.5 py-1 rounded-full hover:bg-blue-200"
            >
              Connect GitHub for company search
            </a>
          </div>
        )}
      </div>
    );
  }

  // Resume uploaded, just GitHub missing — show a small hint
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
      <span className="font-medium text-gray-700">Unlock more:</span>
      <a
        href={`https://reporadar-production.up.railway.app/api/auth/github/start/?token=${localStorage.getItem('auth_token') || ''}`}
        className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
      >
        Connect GitHub for company search
      </a>
    </div>
  );
}
