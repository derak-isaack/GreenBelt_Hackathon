import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useActor } from './useActor';
import type { Resource, WhistleblowerReport, DashboardData } from '../backend';

export function useGetResources() {
  const { actor, isFetching } = useActor();

  return useQuery<Resource[]>({
    queryKey: ['resources'],
    queryFn: async () => {
      if (!actor) return [];
      return actor.getResources();
    },
    enabled: !!actor && !isFetching,
  });
}

export function useGetReports() {
  const { actor, isFetching } = useActor();

  return useQuery<WhistleblowerReport[]>({
    queryKey: ['reports'],
    queryFn: async () => {
      if (!actor) return [];
      return actor.getReports();
    },
    enabled: !!actor && !isFetching,
  });
}

export function useGetDashboardData() {
  const { actor, isFetching } = useActor();

  return useQuery<DashboardData[]>({
    queryKey: ['dashboardData'],
    queryFn: async () => {
      if (!actor) return [];
      return actor.getDashboardData();
    },
    enabled: !!actor && !isFetching,
  });
}

export function useSubmitReport() {
  const { actor } = useActor();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, location, incidentDetails }: { id: string; location: string; incidentDetails: string }) => {
      if (!actor) throw new Error('Actor not initialized');
      return actor.submitReport(id, location, incidentDetails);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });
}
