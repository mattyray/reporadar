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

  const { data: resumeProfile } = useQuery({
    queryKey: ['resumeProfile'],
    queryFn: api.getResumeProfile,
  });

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Settings</h2>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Profile</h3>
        {user && (
          <div className="space-y-2 text-sm text-gray-600">
            <p><span className="font-medium text-gray-900">Email:</span> {user.email}</p>
            <p><span className="font-medium text-gray-900">Name:</span> {user.first_name} {user.last_name}</p>
            <p>
              <span className="font-medium text-gray-900">GitHub:</span>{' '}
              {user.github_connected ? (
                <span className="text-green-600">Connected</span>
              ) : (
                <a href="/api/auth/github/connect/" className="text-indigo-600 hover:underline">
                  Connect GitHub
                </a>
              )}
            </p>
          </div>
        )}
      </div>

      <APIKeySection provider="hunter" label="Hunter.io" queryClient={queryClient} apiKeys={apiKeys} />
      <APIKeySection provider="apollo" label="Apollo.io" queryClient={queryClient} apiKeys={apiKeys} />

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Resume</h3>
        <ResumeUpload queryClient={queryClient} hasResume={!!resumeProfile} />
      </div>
    </div>
  );
}

function APIKeySection({
  provider,
  label,
  queryClient,
  apiKeys,
}: {
  provider: string;
  label: string;
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
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">{label} API Key</h3>
      {existing ? (
        <div className="flex items-center justify-between">
          <span className="text-sm text-green-600">Key configured</span>
          <button
            onClick={() => deleteKey.mutate()}
            className="text-sm text-red-600 hover:underline cursor-pointer"
          >
            Remove
          </button>
        </div>
      ) : (
        <div className="flex gap-2">
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder={`Enter your ${label} API key`}
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

function ResumeUpload({
  queryClient,
  hasResume,
}: {
  queryClient: ReturnType<typeof useQueryClient>;
  hasResume: boolean;
}) {
  const upload = useMutation({
    mutationFn: (file: File) => api.uploadResume(file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['resumeProfile'] }),
  });

  const deleteResume = useMutation({
    mutationFn: api.deleteResume,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['resumeProfile'] }),
  });

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload.mutate(file);
  };

  if (hasResume) {
    return (
      <div className="flex items-center justify-between">
        <span className="text-sm text-green-600">Resume uploaded and parsed</span>
        <button
          onClick={() => deleteResume.mutate()}
          className="text-sm text-red-600 hover:underline cursor-pointer"
        >
          Delete
        </button>
      </div>
    );
  }

  return (
    <div>
      <p className="text-sm text-gray-600 mb-3">
        Upload your resume (PDF or DOCX) to enable personalized outreach messages.
      </p>
      <input
        type="file"
        accept=".pdf,.docx"
        onChange={handleFile}
        className="text-sm"
      />
      {upload.isPending && <p className="text-sm text-gray-500 mt-2">Uploading and parsing...</p>}
      {upload.isError && <p className="text-sm text-red-600 mt-2">{upload.error.message}</p>}
    </div>
  );
}
