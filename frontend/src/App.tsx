import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import LoginPage from './app/LoginPage';
import AuthCallbackPage from './app/AuthCallbackPage';
import SearchPage from './app/SearchPage';
import ProspectsPage from './app/ProspectsPage';
import ProspectDetailPage from './app/ProspectDetailPage';
import SettingsPage from './app/SettingsPage';
import OutreachPage from './app/OutreachPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <p className="text-gray-500 text-center mt-20">Loading...</p>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<SearchPage />} />
        <Route path="prospects" element={<ProspectsPage />} />
        <Route path="prospects/:id" element={<ProspectDetailPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="outreach" element={<OutreachPage />} />
      </Route>
    </Routes>
  );
}
