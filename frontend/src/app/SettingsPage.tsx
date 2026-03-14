import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function SettingsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const githubStatus = searchParams.get('github');

  // After GitHub OAuth redirect, refetch profile to pick up github_connected
  useEffect(() => {
    if (githubStatus) {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      // Clean up the URL
      setSearchParams({}, { replace: true });
    }
  }, [githubStatus, queryClient, setSearchParams]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
        <p className="text-sm text-gray-500 mt-1">Manage your account and connected services.</p>
      </div>

      {/* Profile & Connected Services */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Account</h3>
        {user && (
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <div>
                <p className="text-sm font-medium text-gray-900">Email</p>
                <p className="text-sm text-gray-500">{user.email}</p>
              </div>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <div>
                <p className="text-sm font-medium text-gray-900">Name</p>
                <p className="text-sm text-gray-500">
                  {user.first_name || user.last_name
                    ? `${user.first_name} ${user.last_name}`.trim()
                    : 'Not set'}
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium text-gray-900">GitHub</p>
                <p className="text-sm text-gray-500">
                  {user.github_connected
                    ? 'Connected — used for company search'
                    : 'Not connected — optional, needed for company search'}
                </p>
              </div>
              {user.github_connected ? (
                <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded">
                  Connected
                </span>
              ) : (
                <a
                  href={`https://reporadar-production.up.railway.app/api/auth/github/start/?token=${localStorage.getItem('auth_token') || ''}`}
                  className="bg-gray-900 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-gray-800"
                >
                  Connect GitHub
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
