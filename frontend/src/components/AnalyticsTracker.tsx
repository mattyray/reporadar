import { useLocation } from 'react-router-dom';
import { useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';
const TRACK_URL = `${API_BASE}/api/analytics/track/`;

function beacon(data: Record<string, unknown>) {
  const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
  navigator.sendBeacon(TRACK_URL, blob);
}

export default function AnalyticsTracker() {
  const location = useLocation();
  const pageViewId = useRef<number | null>(null);
  const enteredAt = useRef<number>(Date.now());

  useEffect(() => {
    // Send time-on-page for PREVIOUS page
    if (pageViewId.current) {
      const timeOnPage = (Date.now() - enteredAt.current) / 1000;
      beacon({ page_view_id: pageViewId.current, time_on_page: timeOnPage });
    }

    // Track NEW page
    enteredAt.current = Date.now();
    const fullPath = location.pathname + location.search;

    fetch(TRACK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: fullPath,
        title: document.title,
        referrer: document.referrer,
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        pageViewId.current = data.page_view_id;
      })
      .catch(() => {});

    // Send time-on-page on tab close
    const handleBeforeUnload = () => {
      if (pageViewId.current) {
        const timeOnPage = (Date.now() - enteredAt.current) / 1000;
        beacon({ page_view_id: pageViewId.current, time_on_page: timeOnPage });
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [location.pathname, location.search]);

  return null;
}
