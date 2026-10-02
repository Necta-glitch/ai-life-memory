import React, { useState, useCallback } from 'react';
import { chatApi } from '@/api/chat';
import { memoriesApi } from '@/api/memories';
import type { MemoryResponse, RAGAnswerResponse } from '@/types/api';
import { AskView } from './ask-view';

export default function AskScreen() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<MemoryResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async () => {
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    setAnswer(null);
    setSources([]);

    try {
      const response: RAGAnswerResponse = await chatApi.chat({ query: query.trim() });
      
      setAnswer(response.answer);

      if (response.sources.length > 0) {
        const memoryIds = response.sources.map((s) => s.memory_id);
        const memories: MemoryResponse[] = [];
        
        for (const id of memoryIds) {
          try {
            const memory = await memoriesApi.get(id);
            memories.push(memory);
          } catch (err) {
            console.warn(`Failed to fetch memory ${id}:`, err);
          }
        }
        
        // Sort memories by the order in sources
        memories.sort((a, b) => {
          const indexA = response.sources.findIndex((s) => s.memory_id === a.id);
          const indexB = response.sources.findIndex((s) => s.memory_id === b.id);
          return indexA - indexB;
        });
        
        setSources(memories);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get answer';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [query, loading]);

  const handleRetry = useCallback(() => {
    handleSubmit();
  }, [handleSubmit]);

  const canSubmit = query.trim().length > 0 && !loading;

  return (
    <AskView
      query={query}
      onQueryChange={setQuery}
      onSubmit={handleSubmit}
      canSubmit={canSubmit}
      answer={answer}
      sources={sources}
      loading={loading}
      error={error}
      onRetry={handleRetry}
    />
  );
}