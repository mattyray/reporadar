import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');

  useEffect(() => {
    // After OAuth, the backend redirects here with ?token=<jwt>
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('auth_token', token);
      navigate('/dashboard', { replace: true });
      return;
    }

    // No token in URL — OAuth failed
    setError('Authentication failed. Please try again.');
    setTimeout(() => navigate('/login', { replace: true }), 2000);
  }, [navigate, searchParams]);

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
