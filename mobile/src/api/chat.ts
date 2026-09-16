// Chat/RAG API
import { api } from './client';

export const chatApi = {
  /**
   * Generate a grounded answer using RAG (Retrieval-Augmented Generation).
   * Performs hybrid search, builds RAG context, and generates a grounded answer.
   */
  chat: (request: { query: string; top_k?: number }): Promise<{
    answer: string;
    sources: { memory_id: number; rrf_score: number }[];
    query: string;
    total_sources: number;
  }> =>
    api.post<{
      answer: string;
      sources: { memory_id: number; rrf_score: number }[];
      query: string;
      total_sources: number;
    }>('/search/chat', request).then(res => res.data),
};

export default chatApi;