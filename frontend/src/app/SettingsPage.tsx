import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useAuth } from '../hooks/useAuth';

export default function SettingsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: apiKeys } = useQuery({
    queryKey: ['apiKeys'],
    queryFn: api.getApiKeys,
  });

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
                    ? 'Connected — used for searching GitHub organizations'
                    : 'Not connected — required to search GitHub'}
                </p>
              </div>
              {user.github_connected ? (
                <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded">
                  Connected
                </span>
              ) : (
                <a
                  href="/api/auth/github/connect/"
                  className="bg-gray-900 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-gray-800"
                >
                  Connect GitHub
                </a>
              )}
            </div>
          </div>
        )}
      </div>

      {/* API Keys */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-1">API Keys</h3>
        <p className="text-sm text-gray-500 mb-4">
          Add your own API keys to unlock contact enrichment and other premium features.
          Your keys are encrypted and never shared.
        </p>
        <div className="space-y-4">
          <APIKeyRow
            provider="hunter"
            label="Hunter.io"
            description="Find verified email addresses for engineering contacts"
            queryClient={queryClient}
            apiKeys={apiKeys}
          />
          <div className="border-t border-gray-100" />
          <APIKeyRow
            provider="apollo"
            label="Apollo.io"
            description="Access 210M+ contacts with email and phone data"
            queryClient={queryClient}
            apiKeys={apiKeys}
          />
        </div>
      </div>
    </div>
  );
}

function APIKeyRow({
  provider,
  label,
  description,
  queryClient,
  apiKeys,
}: {
  provider: string;
  label: string;
  description: string;
  queryClient: ReturnType<typeof useQueryClient>;
  apiKeys: any[] | undefined;
}) {
  const [key, setKey] = useState('');
  const existing = apiKeys?.find((k: any) => k.provider === provider);

  const addKey = useMutation({
    mutationFn: () => api.addApiKey(provider, key),
    onSuccess: () => {
      setKey('');
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
    },
  });

  const deleteKey = useMutation({
    mutationFn: () => api.deleteApiKey(provider),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['apiKeys'] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-900">{label}</p>
          <p className="text-xs text-gray-500">{description}</p>
        </div>
        {existing && (
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded">
              Configured
            </span>
            <button
              onClick={() => deleteKey.mutate()}
              className="text-xs text-red-600 hover:underline cursor-pointer"
            >
              Remove
            </button>
          </div>
        )}
      </div>
      {!existing && (
        <div className="flex gap-2 mt-2">
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder={`Paste your ${label} API key`}
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          <button
            onClick={() => addKey.mutate()}
            disabled={!key}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 cursor-pointer"
          >
            Save
          </button>
        </div>
      )}
    </div>
  );
}
