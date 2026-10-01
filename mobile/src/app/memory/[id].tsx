import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, Pressable, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { memoriesApi } from '@/api/memories';
import type { MemoryResponse } from '@/types/api';
import { DetailsView } from '@/components/details-screen/DetailsView';

export default function MemoryDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();

  const memoryId = id ? parseInt(id, 10) : null;

  const [memory, setMemory] = useState<MemoryResponse | null>(null);
  const [isSaved, setIsSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const fetchMemory = async () => {
      if (!memoryId) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const [memoryData, savedMemories] = await Promise.all([
          memoriesApi.get(memoryId),
          memoriesApi.getSaved(),
        ]);

        if (!cancelled && memoryData) {
          setMemory(memoryData);
          const isCurrentlySaved = savedMemories.some((m) => m.id === memoryId);
          setIsSaved(isCurrentlySaved);
        }
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Failed to load memory';
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchMemory();

    return () => {
      cancelled = true;
    };
  }, [memoryId, retryKey]);

  const handleRetry = () => {
    setRetryKey((prev) => prev + 1);
  };

  const handleToggleSave = useCallback(async () => {
    if (!memoryId || saving) return;

    setSaving(true);

    try {
      if (isSaved) {
        await memoriesApi.unsave(memoryId);
        setIsSaved(false);
      } else {
        await memoriesApi.save(memoryId);
        setIsSaved(true);
      }
    } catch (err) {
      console.error('Failed to toggle save:', err);
    } finally {
      setSaving(false);
    }
  }, [memoryId, isSaved, saving]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#a95c49" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  if (error || !memory) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Unable to load memory.</Text>
        {error && <Text style={styles.errorDetail}>{error}</Text>}
        <Pressable style={styles.retryButton} onPress={handleRetry}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <DetailsView
      memory={memory}
      isSaved={isSaved}
      onBack={() => router.back()}
      onToggleSave={handleToggleSave}
      saving={saving}
    />
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f6f3ed',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#f6f3ed',
  },
  errorText: {
    fontSize: 18,
    color: '#d32f2f',
    textAlign: 'center',
    marginBottom: 8,
  },
  errorDetail: {
    fontSize: 13,
    color: '#8f8981',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#a95c49',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fffaf5',
    fontSize: 14,
    fontWeight: '600',
  },
});