import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { UserProfile } from '../types/api';

export function useAuth() {
  const queryClient = useQueryClient();
  const token = localStorage.getItem('auth_token');

  const { data: user, isLoading } = useQuery<UserProfile>({
    queryKey: ['profile'],
    queryFn: api.getProfile,
    enabled: !!token,
  });

  const logout = () => {
    localStorage.removeItem('auth_token');
    queryClient.clear();
    window.location.href = '/login';
  };

  return {
    user: user ?? null,
    isAuthenticated: !!token && !!user,
    isLoading: !!token && isLoading,
    logout,
  };
}
