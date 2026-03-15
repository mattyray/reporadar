import { useLocation } from 'react-router-dom';
import { useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';
const TRACK_URL = `${API_BASE}/api/analytics/track/`;

function sendBeaconData(data: Record<string, unknown>) {
  const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
  if (navigator.sendBeacon) {
    navigator.sendBeacon(TRACK_URL, blob);
  } else {
    // Fallback for older browsers
    fetch(TRACK_URL, {
      method: 'POST',
      body: blob,
      keepalive: true,
    }).catch(() => {});
  }
}

function getUtmParams(search: string): Record<string, string> {
  const params = new URLSearchParams(search);
  const utm: Record<string, string> = {};
  for (const key of ['utm_source', 'utm_medium', 'utm_campaign']) {
    const val = params.get(key);
    if (val) utm[key] = val;
  }
  return utm;
}

export default function AnalyticsTracker() {
  const location = useLocation();
  const pageViewId = useRef<number | null>(null);
  const enteredAt = useRef<number>(Date.now());
  const lastTrackedPath = useRef<string>('');

  // Effect 1: Page navigation tracking
  useEffect(() => {
    const fullPath = location.pathname + location.search;

    // Deduplicate — skip if same path fires twice
    if (fullPath === lastTrackedPath.current) return;

    // Send "leave" beacon for PREVIOUS page
    if (pageViewId.current && lastTrackedPath.current) {
      const timeOnPage = (Date.now() - enteredAt.current) / 1000;
      sendBeaconData({
        type: 'leave',
        page_view_id: pageViewId.current,
        time_on_page: timeOnPage,
      });
    }

    lastTrackedPath.current = fullPath;
    enteredAt.current = Date.now();
    pageViewId.current = null;

    // Track NEW page
    const payload: Record<string, unknown> = {
      type: 'view',
      path: fullPath,
      title: document.title,
      referrer: document.referrer,
      screen_width: window.screen.width,
      screen_height: window.screen.height,
      ...getUtmParams(location.search),
    };

    fetch(TRACK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        pageViewId.current = data.page_view_id;
      })
      .catch(() => {});
  }, [location.pathname, location.search]);

  // Effect 2: Page unload / tab switch
  useEffect(() => {
    const sendLeave = () => {
      if (pageViewId.current) {
        const timeOnPage = (Date.now() - enteredAt.current) / 1000;
        sendBeaconData({
          type: 'leave',
          page_view_id: pageViewId.current,
          time_on_page: timeOnPage,
        });
      }
    };

    const handleBeforeUnload = () => sendLeave();
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') sendLeave();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return null;
}
