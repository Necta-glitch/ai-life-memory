// API Types for AI Life Memory Mobile App

// Base memory types
export interface MemoryResponse {
  id: number;
  user_id: string;
  content: string;
  summary: string | null;
  topics: string[] | null;
  entities: string[] | null;
  source: string;
  created_at: string;
  occurred_at: string | null;
}

export interface MemoryCreate {
  content: string;
  source?: string;
  occurred_at?: string | null;
}

export interface MemoryUpdate {
  content?: string;
  occurred_at?: string | null;
}

// Search types
export interface SemanticSearchRequest {
  query: string;
  top_k?: number;
}

export interface SemanticSearchResult {
  id: number;
  user_id: string;
  content: string;
  summary: string | null;
  topics: string[] | null;
  entities: string[] | null;
  source: string;
  created_at: string;
  occurred_at: string | null;
  similarity: number;
}

export interface SemanticSearchResponse {
  results: SemanticSearchResult[];
  query: string;
  total_candidates: number;
}

export interface KeywordSearchRequest {
  query: string;
  top_k?: number;
}

export interface KeywordSearchResult {
  id: number;
  user_id: string;
  content: string;
  summary: string | null;
  topics: string[] | null;
  entities: string[] | null;
  source: string;
  created_at: string;
  occurred_at: string | null;
  keyword_score: number;
}

export interface KeywordSearchResponse {
  results: KeywordSearchResult[];
  query: string;
  total_candidates: number;
}

export interface HybridSearchRequest {
  query: string;
  top_k?: number;
}

export interface HybridSearchResult {
  id: number;
  user_id: string;
  content: string;
  summary: string | null;
  topics: string[] | null;
  entities: string[] | null;
  source: string;
  created_at: string;
  occurred_at: string | null;
  rrf_score: number;
  rerank_score: number | null;
  embedding: number[] | null;
}

export interface HybridSearchResponse {
  results: HybridSearchResult[];
  query: string;
  total_candidates: number;
}

// RAG types
export interface RAGContextItem {
  memory_id: number;
  content: string;
  summary: string | null;
  topics: string[];
  entities: string[];
  occurred_at: string | null;
  created_at: string;
  rrf_score: number;
}

export interface RAGContext {
  query: string;
  items: RAGContextItem[];
  total_items: number;
}

export interface RAGSource {
  memory_id: number;
  rrf_score: number;
}

export interface RAGAnswerRequest {
  query: string;
  top_k?: number;
}

export interface RAGAnswerResponse {
  answer: string;
  sources: {
    memory_id: number;
    rrf_score: number;
  }[];
  query: string;
  total_sources: number;
}