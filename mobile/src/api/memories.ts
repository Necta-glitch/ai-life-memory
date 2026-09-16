// Memory API endpoints
import { api } from './client';
import type { MemoryResponse, MemoryCreate, MemoryUpdate } from '@/types/api';

export const memoriesApi = {
  /**
   * Get all memories for the current user
   */
  list: (): Promise<MemoryResponse[]> => api.get<MemoryResponse[]>('/memories/').then(res => res.data),

  /**
   * Get a single memory by ID
   */
  get: (id: number): Promise<MemoryResponse> => api.get<MemoryResponse>(`/memories/${id}`).then(res => res.data),

  /**
   * Create a new memory
   */
  create: (data: MemoryCreate): Promise<MemoryResponse> =>
    api.post<MemoryResponse>('/memories/', {
      content: data.content,
      source: data.source || 'text',
      occurred_at: data.occurred_at || null,
    }).then(res => res.data),

  /**
   * Update a memory by ID
   */
  update: (id: number, data: MemoryUpdate): Promise<MemoryResponse> =>
    api.put<MemoryResponse>(`/memories/${id}`, data).then(res => res.data),

  /**
   * Delete a memory by ID
   */
  delete: (id: number): Promise<void> => api.delete(`/memories/${id}`).then(res => res.data),
};

export default memoriesApi;