import { FlatList, RefreshControl, StyleSheet, Text, View, ActivityIndicator, TouchableOpacity } from 'react-native';
import { memoriesApi } from '@/api/memories';
import type { MemoryResponse } from '@/types/api';
import { MemoryItem } from '@/components/MemoryItem';
import React from 'react';

export default function MemoriesScreen() {
  const [memories, setMemories] = React.useState<MemoryResponse[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const fetchMemories = async (): Promise<MemoryResponse[]> => {
    const data = await memoriesApi.list();
    return data;
  };

  const loadMemories = async (isRefresh = false) => {
    if (!isRefresh) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError(null);

    try {
      const data = await fetchMemories();
      setMemories(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load memories';
      setError(message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  React.useEffect(() => {
    let mounted = true;

    const loadInitialMemories = async () => {
      try {
        const data = await fetchMemories();
        if (mounted) {
          setMemories(data);
        }
      } catch (err) {
        if (mounted) {
          const message = err instanceof Error ? err.message : 'Failed to load memories';
          setError(message);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadInitialMemories();

    return () => {
      mounted = false;
    };
  }, []);

  const onRefresh = () => loadMemories(true);
  const onRetry = () => loadMemories();

  if (loading && memories.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading memories...</Text>
      </View>
    );
  }

  if (error && memories.length === 0) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>Error: {error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (memories.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No memories yet</Text>
        <Text style={styles.emptySubtext}>Pull to refresh or add a memory</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={memories}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => <MemoryItem memory={item} />}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={styles.listContent}
        ListFooterComponent={
          !loading && !refreshing && memories.length > 0 ? (
            <View style={styles.footer}>
              <Text style={styles.footerText}>{memories.length} memory{memories.length !== 1 ? 's' : ''}</Text>
            </View>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  listContent: {
    paddingBottom: 16,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
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
  },
  errorText: {
    fontSize: 16,
    color: '#d32f2f',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
  },
  footer: {
    padding: 16,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#999',
  },
});