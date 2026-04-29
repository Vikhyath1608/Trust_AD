import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/services/serverApi';

export function useServerHealth() {
  const { data, isError, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.ping,
    refetchInterval: 15_000,
    retry: 0,
  });
  const status = isLoading ? 'pending' : isError ? 'offline' : 'online';
  return { status } as const;
}
