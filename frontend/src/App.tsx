import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import LandingPage from './app/LandingPage';
import LoginPage from './app/LoginPage';
import AuthCallbackPage from './app/AuthCallbackPage';
import SearchPage from './app/SearchPage';
import ProspectsPage from './app/ProspectsPage';
import ProspectDetailPage from './app/ProspectDetailPage';
import SettingsPage from './app/SettingsPage';
import OutreachPage from './app/OutreachPage';
import JobsPage from './app/JobsPage';

function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <h1 className="text-4xl font-bold text-gray-800 mb-2">404</h1>
      <p className="text-gray-500 mb-4">Page not found</p>
      <a href="/dashboard" className="text-indigo-600 hover:text-indigo-700 underline">
        Go to dashboard
      </a>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <p className="text-gray-500 text-center mt-20">Loading...</p>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<SearchPage />} />
        <Route path="prospects" element={<ProspectsPage />} />
        <Route path="prospects/:id" element={<ProspectDetailPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="outreach" element={<OutreachPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
