// API Configuration
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  // Memories
  MEMORIES: '/memories',
  MEMORY_BY_ID: (id: number) => `/memories/${id}`,
  MEMORIES_VOICE: '/memories/voice',
  
  // Search
  SEARCH_SEMANTIC: '/search/semantic',
  SEARCH_KEYWORD: '/search/keyword',
  SEARCH_HYBRID: '/search/hybrid',
  SEARCH_RERANK: '/search/rerank',
  SEARCH_CHAT: '/search/chat',
} as const;