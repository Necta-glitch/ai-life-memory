import { Text, View, StyleSheet, TouchableOpacity } from 'react-native';
import type { MemoryResponse } from '@/types/api';

interface MemoryItemProps {
  memory: MemoryResponse;
  onPress?: () => void;
}

export function MemoryItem({ memory, onPress }: MemoryItemProps) {
  const displayDate = memory.occurred_at || memory.created_at;
  const formattedDate = new Date(displayDate).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  const Content = onPress ? TouchableOpacity : View;

  return (
    <Content style={styles.container} onPress={onPress} activeOpacity={0.8}>
      <View style={styles.contentContainer}>
        <Text style={styles.content} numberOfLines={3}>
          {memory.content}
        </Text>
        {memory.summary && (
          <Text style={styles.summary} numberOfLines={2}>
            {memory.summary}
          </Text>
        )}
      </View>
      <View style={styles.metaContainer}>
        <Text style={styles.source}>{memory.source}</Text>
        <Text style={styles.date}>{formattedDate}</Text>
      </View>
    </Content>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    backgroundColor: '#fff',
  },
  contentContainer: {
    marginBottom: 8,
  },
  content: {
    fontSize: 16,
    color: '#1a1a1a',
    lineHeight: 22,
    marginBottom: 4,
  },
  summary: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    fontStyle: 'italic',
  },
  metaContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  source: {
    fontSize: 12,
    color: '#999',
    textTransform: 'capitalize',
  },
  date: {
    fontSize: 12,
    color: '#999',
  },
});