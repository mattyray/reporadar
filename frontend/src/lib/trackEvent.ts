const API_BASE = import.meta.env.VITE_API_URL || '';
const EVENT_URL = `${API_BASE}/api/analytics/event/`;

type EventCategory = 'job' | 'search' | 'company' | 'resume' | 'auth' | 'nav';

interface TrackEventParams {
  eventType: string;
  category: EventCategory;
  label?: string;
  value?: number;
  metadata?: Record<string, string | number | boolean | string[]>;
}

export function trackEvent({ eventType, category, label, value, metadata }: TrackEventParams) {
  const payload: Record<string, unknown> = {
    event_type: eventType,
    category,
  };
  if (label) payload.label = label;
  if (value !== undefined) payload.value = value;
  if (metadata) payload.metadata = metadata;

  // Fire and forget — never block UI
  fetch(EVENT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => {});
}
