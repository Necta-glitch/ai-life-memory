import { StyleSheet, Text, View, TextInput, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { memoriesApi } from '@/api/memories';
import type { MemoryCreate } from '@/types/api';
import React from 'react';

export default function CreateMemoryScreen() {
  const router = useRouter();
  const [content, setContent] = React.useState('');
  const [occurredAt, setOccurredAt] = React.useState('');
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const trimmedContent = content.trim();
  const isValid = trimmedContent.length > 0;

  const handleSubmit = async () => {
    if (!isValid || submitting) return;

    setSubmitting(true);
    setError(null);

    try {
      const memoryData: MemoryCreate = {
        content: trimmedContent,
        source: 'text',
        occurred_at: occurredAt.trim() ? new Date(occurredAt.trim()).toISOString() : null,
      };

      await memoriesApi.create(memoryData);
      router.back();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create memory';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()} accessibilityLabel="Back">
          <Text style={styles.backButtonText}>Cancel</Text>
        </TouchableOpacity>
        <Text style={styles.title}>New Memory</Text>
        <TouchableOpacity 
          style={[styles.saveButton, !isValid && styles.saveButtonDisabled]} 
          onPress={handleSubmit}
          disabled={!isValid || submitting}
          accessibilityLabel={submitting ? 'Saving...' : 'Save'}
        >
          {submitting ? (
            <ActivityIndicator size={20} color="#fff" />
          ) : (
            <Text style={styles.saveButtonText}>Save</Text>
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.formContainer}>
        <TextInput
          style={styles.textInput}
          multiline
          placeholder="What's on your mind?"
          value={content}
          onChangeText={setContent}
          placeholderTextColor="#999"
          autoFocus
          maxLength={10000}
        />

        <View style={styles.dateContainer}>
          <Text style={styles.dateLabel}>When did this happen? (optional)</Text>
          <TextInput
            style={styles.dateInput}
            placeholder="YYYY-MM-DD"
            value={occurredAt}
            onChangeText={setOccurredAt}
            placeholderTextColor="#999"
            keyboardType="default"
            autoCapitalize="none"
          />
          {occurredAt && (
            <TouchableOpacity style={styles.clearDateButton} onPress={() => setOccurredAt('')}>
              <Text style={styles.clearDateButtonText}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        <View style={styles.hintContainer}>
          <Text style={styles.hintText}>
            {trimmedContent.length}/10000 characters
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    backgroundColor: '#fff',
  },
  backButton: {
    padding: 8,
  },
  backButtonText: {
    fontSize: 16,
    color: '#007AFF',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  saveButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  saveButtonDisabled: {
    backgroundColor: '#ccc',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  formContainer: {
    flex: 1,
    padding: 16,
  },
  textInput: {
    flex: 1,
    minHeight: 200,
    padding: 16,
    fontSize: 16,
    color: '#1a1a1a',
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    textAlignVertical: 'top',
  },
  dateContainer: {
    marginTop: 16,
  },
  dateLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  dateInput: {
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    fontSize: 16,
    color: '#1a1a1a',
  },
  clearDateButton: {
    marginTop: 8,
    paddingVertical: 8,
    alignItems: 'center',
  },
  clearDateButtonText: {
    fontSize: 14,
    color: '#007AFF',
  },
  errorContainer: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#fef2f2',
    borderRadius: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#d32f2f',
  },
  hintContainer: {
    marginTop: 16,
    alignItems: 'flex-end',
  },
  hintText: {
    fontSize: 12,
    color: '#999',
  },
});