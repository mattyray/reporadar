import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    // After OAuth redirect, allauth has set a session cookie.
    // Fetch the session to get the JWT access token.
    async function fetchSession() {
      try {
        const res = await fetch('/_allauth/browser/v1/auth/session', {
          credentials: 'include',
        });
        if (res.ok) {
          const data = await res.json();
          // allauth headless returns session token in meta or data
          const token =
            data?.meta?.access_token ||
            data?.meta?.session_token ||
            data?.data?.session_token;
          if (token) {
            localStorage.setItem('auth_token', token);
            navigate('/dashboard', { replace: true });
            return;
          }
        }
        // If we couldn't get a token from the session, the OAuth may have failed
        setError('Authentication failed. Please try again.');
        setTimeout(() => navigate('/login', { replace: true }), 2000);
      } catch {
        setError('Could not connect to server.');
        setTimeout(() => navigate('/login', { replace: true }), 2000);
      }
    }

    fetchSession();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        {error ? (
          <p className="text-red-600">{error}</p>
        ) : (
          <p className="text-gray-500">Authenticating...</p>
        )}
      </div>
    </div>
  );
}
