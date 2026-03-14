import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { OutreachMessage, Organization } from '../types/api';

function ResumeSection({ queryClient }: { queryClient: ReturnType<typeof useQueryClient> }) {
  const { data: resumeProfile, isLoading } = useQuery({
    queryKey: ['resumeProfile'],
    queryFn: api.getResumeProfile,
    retry: false,
  });

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

  if (isLoading) return null;

  if (resumeProfile) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-green-800">Resume uploaded</p>
          <p className="text-xs text-green-600 mt-0.5">
            Your outreach messages will be personalized based on your experience.
          </p>
        </div>
        <button
          onClick={() => deleteResume.mutate()}
          className="text-xs text-red-600 hover:underline cursor-pointer"
        >
          Remove
        </button>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <p className="text-sm font-medium text-blue-900 mb-1">Upload your resume for personalized messages</p>
      <p className="text-xs text-blue-700 mb-3">
        We'll use AI to match your skills and experience to each company, creating tailored outreach
        that mentions specific projects and technologies you have in common.
      </p>
      <label className="inline-flex items-center gap-2 bg-blue-600 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-blue-700 cursor-pointer">
        <span>Choose file (PDF or DOCX)</span>
        <input type="file" accept=".pdf,.docx" onChange={handleFile} className="hidden" />
      </label>
      {upload.isPending && <p className="text-xs text-blue-600 mt-2">Uploading and parsing...</p>}
      {upload.isError && <p className="text-xs text-red-600 mt-2">{upload.error.message}</p>}
    </div>
  );
}

export default function OutreachPage() {
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const initialOrgId = searchParams.get('orgId') || '';

  const [orgId, setOrgId] = useState(initialOrgId);
  const [contactId, setContactId] = useState('');
  const [messageType, setMessageType] = useState('email');
  const [generatedMessage, setGeneratedMessage] = useState<OutreachMessage | null>(null);
  const [pollingId, setPollingId] = useState<string | null>(null);

  const { data: prospects } = useQuery({
    queryKey: ['prospects'],
    queryFn: api.getProspects,
  });

  const { data: contacts } = useQuery({
    queryKey: ['contacts', orgId],
    queryFn: () => api.getContacts(Number(orgId)),
    enabled: !!orgId,
  });

  const { data: history } = useQuery({
    queryKey: ['outreachHistory'],
    queryFn: api.getOutreachHistory,
  });

  // Poll for outreach generation completion
  const { data: polledMessage } = useQuery({
    queryKey: ['outreachStatus', pollingId],
    queryFn: () => api.getOutreachStatus(pollingId!),
    enabled: !!pollingId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') return false;
      return 2000;
    },
  });

  useEffect(() => {
    if (polledMessage && (polledMessage.status === 'completed' || polledMessage.status === 'failed')) {
      setGeneratedMessage(polledMessage);
      setPollingId(null);
      queryClient.invalidateQueries({ queryKey: ['outreachHistory'] });
    }
  }, [polledMessage, queryClient]);

  const generate = useMutation({
    mutationFn: () => api.generateOutreach(Number(orgId), messageType, contactId ? Number(contactId) : undefined),
    onSuccess: (data) => {
      if (data.status === 'generating') {
        setPollingId(data.id);
        setGeneratedMessage(null);
      } else {
        setGeneratedMessage(data);
        queryClient.invalidateQueries({ queryKey: ['outreachHistory'] });
      }
    },
  });

  const isGenerating = generate.isPending || !!pollingId;

  const orgs = prospects?.results ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Outreach</h2>
        <p className="text-sm text-gray-500 mt-1">
          Generate personalized messages to reach out to companies you've discovered.
        </p>
      </div>

      <ResumeSection queryClient={queryClient} />

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Generate Message</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Organization</label>
            {orgs.length > 0 ? (
              <select
                value={orgId}
                onChange={(e) => { setOrgId(e.target.value); setContactId(''); }}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="">Select an organization...</option>
                {orgs.map((org: Organization) => (
                  <option key={org.id} value={org.id}>
                    {org.name || org.github_login}
                  </option>
                ))}
              </select>
            ) : (
              <div>
                <input
                  type="number"
                  value={orgId}
                  onChange={(e) => { setOrgId(e.target.value); setContactId(''); }}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  placeholder="Organization ID"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Run a search first to discover organizations.
                </p>
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Recipient</label>
            <select
              value={contactId}
              onChange={(e) => setContactId(e.target.value)}
              disabled={!orgId}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm disabled:opacity-50"
            >
              <option value="">Hiring Manager (default)</option>
              {(contacts ?? []).map((c: any) => (
                <option key={c.id} value={c.id}>
                  {c.first_name} {c.last_name}{c.position ? ` — ${c.position}` : ''}
                </option>
              ))}
            </select>
            {orgId && contacts && contacts.length === 0 && (
              <p className="text-xs text-gray-400 mt-1">No contacts enriched yet.</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Message Type</label>
            <select
              value={messageType}
              onChange={(e) => setMessageType(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="email">Cold Email</option>
              <option value="linkedin_dm">LinkedIn Message</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        <button
          onClick={() => generate.mutate()}
          disabled={!orgId || isGenerating}
          className="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 disabled:opacity-50 cursor-pointer"
        >
          {isGenerating ? 'Generating...' : 'Generate Message'}
        </button>
      </div>

      {generate.isError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
          {generate.error.message}
        </div>
      )}

      {generatedMessage && generatedMessage.status === 'failed' && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
          Message generation failed: {generatedMessage.error || 'Unknown error'}
        </div>
      )}

      {generatedMessage && generatedMessage.status === 'completed' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-medium text-gray-900">
              {generatedMessage.subject || generatedMessage.message_type}
            </h3>
            <button
              onClick={() => {
                const text = generatedMessage.subject
                  ? `Subject: ${generatedMessage.subject}\n\n${generatedMessage.body}`
                  : generatedMessage.body;
                navigator.clipboard.writeText(text);
              }}
              className="text-xs text-indigo-600 hover:underline cursor-pointer"
            >
              Copy to clipboard
            </button>
          </div>
          <p className="text-xs text-gray-500 mb-4">
            {generatedMessage.message_type} for {generatedMessage.organization_name}
          </p>
          <div className="bg-gray-50 rounded-md p-4 text-sm text-gray-800 whitespace-pre-wrap">
            {generatedMessage.body}
          </div>
        </div>
      )}

      {history?.results && history.results.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">History</h3>
          {history.results.map((m: OutreachMessage) => (
            <div key={m.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm text-gray-900">{m.subject}</span>
                <span className="text-xs text-gray-500">
                  {new Date(m.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-2">
                {m.message_type} — {m.organization_name}
              </p>
              <p className="text-sm text-gray-700 line-clamp-3">{m.body}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
