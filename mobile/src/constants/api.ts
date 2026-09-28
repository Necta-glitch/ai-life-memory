// API Configuration
// EXPO_PUBLIC_API_URL should be set for production.
// For local development, the client handles platform-specific fallbacks:
// - Web: http://localhost:8000
// - iOS Simulator: http://localhost:8000
// - Android Emulator: http://10.0.2.2:8000
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL;

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