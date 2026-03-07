import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { OutreachMessage } from '../types/api';

export default function OutreachPage() {
  const [searchParams] = useSearchParams();
  const initialOrgId = searchParams.get('orgId') || '';

  const [orgId, setOrgId] = useState(initialOrgId);
  const [messageType, setMessageType] = useState('cold_email');
  const [generatedMessage, setGeneratedMessage] = useState<OutreachMessage | null>(null);

  const { data: history } = useQuery({
    queryKey: ['outreachHistory'],
    queryFn: api.getOutreachHistory,
  });

  const generate = useMutation({
    mutationFn: () => api.generateOutreach(Number(orgId), messageType),
    onSuccess: (data) => setGeneratedMessage(data),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Outreach</h2>

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <h3 className="text-lg font-medium text-gray-900">Generate Message</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Organization ID</label>
            <input
              type="number"
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              placeholder="Enter org ID"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Message Type</label>
            <select
              value={messageType}
              onChange={(e) => setMessageType(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="cold_email">Cold Email</option>
              <option value="linkedin_message">LinkedIn Message</option>
              <option value="intro_request">Intro Request</option>
            </select>
          </div>
        </div>
        <button
          onClick={() => generate.mutate()}
          disabled={!orgId || generate.isPending}
          className="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 disabled:opacity-50 cursor-pointer"
        >
          {generate.isPending ? 'Generating...' : 'Generate'}
        </button>
      </div>

      {generate.isError && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 text-sm">
          {generate.error.message}
        </div>
      )}

      {generatedMessage && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">{generatedMessage.subject}</h3>
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
