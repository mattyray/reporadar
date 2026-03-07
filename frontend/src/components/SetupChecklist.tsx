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

  const steps = [
    {
      label: 'Connect GitHub',
      done: user.github_connected,
      description: 'Required to search GitHub organizations and detect tech stacks.',
      action: user.github_connected ? null : (
        <a
          href="/api/auth/github/connect/"
          className="inline-block bg-gray-900 text-white px-3 py-1.5 rounded-md text-sm font-medium hover:bg-gray-800"
        >
          Connect GitHub
        </a>
      ),
    },
    {
      label: 'Upload resume',
      done: !!resumeProfile,
      description: 'Enables AI-personalized outreach messages based on your experience.',
      action: null, // Handled in Outreach page
      hint: 'Go to the Outreach tab to upload.',
    },
    {
      label: 'Add Hunter.io key (optional)',
      done: user.has_hunter_key,
      description: 'Unlock email contact enrichment for discovered organizations.',
      hint: 'Add in Settings.',
    },
  ];

  const allDone = steps.every((s) => s.done);
  if (allDone) return null;

  const completedCount = steps.filter((s) => s.done).length;

  return (
    <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Get started with RepoRadar</h3>
        <span className="text-sm text-gray-500">
          {completedCount}/{steps.length} complete
        </span>
      </div>
      <div className="space-y-4">
        {steps.map((step) => (
          <div key={step.label} className="flex items-start gap-3">
            <div className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
              step.done
                ? 'bg-green-100 text-green-600'
                : 'bg-gray-100 text-gray-400'
            }`}>
              {step.done ? '✓' : '·'}
            </div>
            <div className="flex-1">
              <p className={`text-sm font-medium ${step.done ? 'text-gray-400 line-through' : 'text-gray-900'}`}>
                {step.label}
              </p>
              {!step.done && (
                <p className="text-xs text-gray-500 mt-0.5">{step.description}</p>
              )}
              {!step.done && step.action && (
                <div className="mt-2">{step.action}</div>
              )}
              {!step.done && !step.action && step.hint && (
                <p className="text-xs text-blue-600 mt-1">{step.hint}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
