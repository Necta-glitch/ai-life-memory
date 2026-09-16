// Search API endpoints
import { api } from './client';

export const searchApi = {
  /**
   * Semantic search using vector similarity
   */
  semantic: (query: string, top_k?: number) =>
    api.post<{
      results: {
        id: number;
        user_id: string;
        content: string;
        summary: string | null;
        topics: string[];
        entities: string[];
        source: string;
        created_at: string;
        occurred_at: string | null;
        similarity: number;
      }[];
      query: string;
      total_candidates: number;
    }>('/search/semantic', { query, top_k }),

  /**
   * Keyword search using PostgreSQL Full-Text Search
   */
  keyword: (query: string, top_k?: number) =>
    api.post<{
      results: {
        id: number;
        user_id: string;
        content: string;
        summary: string | null;
        topics: string[];
        entities: string[];
        source: string;
        created_at: string;
        occurred_at: string | null;
        keyword_score: number;
      }[];
      query: string;
      total_candidates: number;
    }>('/search/keyword', { query, top_k }),

  /**
   * Hybrid search combining semantic and keyword search with RRF
   */
  hybrid: (query: string, top_k?: number) =>
    api.post<{
      results: {
        id: number;
        user_id: string;
        content: string;
        summary: string | null;
        topics: string[];
        entities: string[];
        source: string;
        created_at: string;
        occurred_at: string | null;
        rrf_score: number;
      }[];
      query: string;
      total_candidates: number;
    }>('/search/hybrid', { query, top_k }),

  /**
   * Hybrid search with reranking
   */
  rerank: (query: string, top_k?: number) =>
    api.post<{
      results: {
        id: number;
        user_id: string;
        content: string;
        summary: string | null;
        topics: string[];
        entities: string[];
        source: string;
        created_at: string;
        occurred_at: string | null;
        rrf_score: number;
        rerank_score: number;
      }[];
      query: string;
      total_candidates: number;
    }>('/search/rerank', { query, top_k }),

  /**
   * RAG Chat - Generate grounded answer using RAG
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

export default {
  semantic: (query: string, top_k?: number) => api.post<any>('/search/semantic', { query, top_k }),
  keyword: (query: string, top_k?: number) => api.post<any>('/search/keyword', { query, top_k }),
  hybrid: (query: string, top_k?: number) => api.post<any>('/search/hybrid', { query, top_k }),
  rerank: (query: string, top_k?: number) => api.post<any>('/search/rerank', { query, top_k }),
  chat: (query: string, top_k?: number) =>
    api.post<{
      answer: string;
      sources: { memory_id: number; rrf_score: number }[];
      query: string;
      total_sources: number;
    }>('/search/chat', { query, top_k }).then(res => res.data),
};