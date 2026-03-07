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

  const remaining: { label: string; action?: string; href?: string }[] = [];

  if (!user.github_connected) {
    remaining.push({ label: 'Connect GitHub for live search', href: '/api/auth/github/connect/' });
  }
  if (!resumeProfile) {
    remaining.push({ label: 'Upload resume for auto-detect', action: 'Upload above' });
  }
  if (!user.has_hunter_key) {
    remaining.push({ label: 'Add Hunter.io key for email enrichment', action: 'Settings' });
  }

  if (remaining.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
      <span className="font-medium text-gray-700">Unlock more:</span>
      {remaining.map((item) => (
        item.href ? (
          <a
            key={item.label}
            href={item.href}
            className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200"
          >
            {item.label}
          </a>
        ) : (
          <span key={item.label} className="px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full">
            {item.label}
          </span>
        )
      ))}
    </div>
  );
}
