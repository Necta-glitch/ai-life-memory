import React from 'react';
import { View, Text, StyleSheet, Pressable, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft, Bookmark, Check, Headphones, Sparkles } from 'lucide-react-native';
import type { MemoryResponse } from '@/types/api';

interface DetailsViewProps {
  memory: MemoryResponse;
  isSaved: boolean;
  onBack: () => void;
  onToggleSave: () => void;
  saving: boolean;
}

function formatDate(dateString: string | null): { dateLabel: string; time: string; month: string; day: string } {
  const date = dateString ? new Date(dateString) : new Date();
  const dateLabel = date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
  const time = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const month = date.toLocaleDateString('en-US', { month: 'short' }).toUpperCase();
  const day = String(date.getDate()).padStart(2, '0');
  return { dateLabel, time, month, day };
}

function DetailsView({
  memory,
  isSaved,
  onBack,
  onToggleSave,
  saving,
}: DetailsViewProps) {
  const { dateLabel, time, month, day } = formatDate(memory.occurred_at || memory.created_at);
  const isVoice = memory.source === 'voice';

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={onBack} accessibilityLabel="Back" style={styles.backButton}>
          <ArrowLeft size={22} strokeWidth={2} color="#2d2b29" />
        </Pressable>
        <View style={styles.dateColumn}>
          <Text style={styles.dateMonth}>{month}</Text>
          <Text style={styles.dateDay}>{day}</Text>
        </View>
        <Pressable
          onPress={onToggleSave}
          disabled={saving}
          accessibilityLabel={isSaved ? 'Unsave memory' : 'Save memory'}
          style={styles.saveButton}
        >
          {isSaved ? (
            <Check size={22} strokeWidth={2.2} color="#a95c49" />
          ) : (
            <Bookmark size={22} strokeWidth={1.7} color="#a39b92" />
          )}
        </Pressable>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
        <View style={styles.memoryCard}>
          <View style={styles.memoryMeta}>
            <Text style={styles.memoryMetaText}>{dateLabel}</Text>
            <Text style={styles.metaDot}>·</Text>
            <Text style={styles.memoryMetaText}>{time}</Text>
          </View>
          <Text style={styles.memoryContent}>{memory.content}</Text>
          {memory.summary && (
            <View style={styles.summaryBox}>
              <View style={styles.summaryLabel}>
                <Sparkles size={12} strokeWidth={1.7} color="#a95c49" />
                <Text style={styles.summaryLabelText}>MEMORY UNDERSTOOD</Text>
              </View>
              <Text style={styles.summaryText}>{memory.summary}</Text>
            </View>
          )}
          {(memory.topics && memory.topics.length > 0) || (memory.entities && memory.entities.length > 0) ? (
            <View style={styles.tagsContainer}>
              {memory.topics && memory.topics.length > 0 && (
                <View style={styles.tagGroup}>
                  <Text style={styles.tagGroupLabel}>TOPICS</Text>
                  <View style={styles.tagsRow}>
                    {memory.topics.map((topic, i) => (
                      <Text key={i} style={styles.tag}>{topic}</Text>
                    ))}
                  </View>
                </View>
              )}
              {memory.entities && memory.entities.length > 0 && (
                <View style={styles.tagGroup}>
                  <Text style={styles.tagGroupLabel}>ENTITIES</Text>
                  <View style={styles.tagsRow}>
                    {memory.entities.map((entity, i) => (
                      <Text key={i} style={styles.tag}>{entity}</Text>
                    ))}
                  </View>
                </View>
              )}
            </View>
          ) : null}
          <View style={styles.cardFooter}>
            {isVoice && (
              <View style={styles.voiceTag}>
                <Headphones size={13} strokeWidth={1.7} color="#8e8982" />
                <Text style={styles.voiceTagText}>VOICE NOTE</Text>
              </View>
            )}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f6f3ed',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 27,
    paddingTop: 27,
    paddingBottom: 16,
  },
  backButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dateColumn: {
    width: 42,
    alignItems: 'center',
  },
  dateMonth: {
    fontFamily: 'DM Mono',
    fontSize: 8,
    fontWeight: '400',
    letterSpacing: 1.12,
    color: '#9d958d',
  },
  dateDay: {
    marginTop: 3,
    fontFamily: 'DM Mono',
    fontSize: 25,
    fontWeight: '400',
    letterSpacing: -2,
    lineHeight: 25,
    color: '#4c4843',
  },
  saveButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 27,
    paddingBottom: 40,
  },
  memoryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  memoryMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-start',
    gap: 7,
    marginBottom: 16,
  },
  memoryMetaText: {
    fontFamily: 'DM Mono',
    fontSize: 9,
    letterSpacing: 0.45,
    color: '#9b948c',
  },
  metaDot: {
    color: '#bd7560',
    fontFamily: 'DM Mono',
    fontSize: 9,
  },
  memoryContent: {
    color: '#312e2b',
    fontFamily: 'Libre Baskerville',
    fontSize: 20,
    fontWeight: '400',
    lineHeight: 28,
    letterSpacing: -0.7,
    marginBottom: 16,
  },
  summaryBox: {
    marginTop: 8,
    padding: 14,
    paddingHorizontal: 16,
    borderLeftWidth: 2,
    borderLeftColor: '#c48672',
    backgroundColor: '#f0e9e0',
    borderRadius: 8,
  },
  summaryLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  summaryLabelText: {
    fontFamily: 'DM Mono',
    fontSize: 8,
    fontWeight: '500',
    letterSpacing: 1.12,
    color: '#a95c49',
  },
  summaryText: {
    margin: 0,
    color: '#665f58',
    fontSize: 13,
    lineHeight: 19.5,
    fontFamily: 'Libre Baskerville',
  },
  tagsContainer: {
    marginTop: 20,
    gap: 16,
  },
  tagGroup: {},
  tagGroupLabel: {
    fontFamily: 'DM Mono',
    fontSize: 8,
    fontWeight: '500',
    letterSpacing: 1.12,
    color: '#a95c49',
    marginBottom: 8,
  },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    backgroundColor: '#eeebe4',
    borderWidth: 1,
    borderColor: '#dad2c8',
    borderRadius: 999,
    fontFamily: 'DM Mono',
    fontSize: 9,
    fontWeight: '500',
    letterSpacing: 0.6,
    color: '#716b64',
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-start',
    gap: 12,
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#ded9d1',
  },
  voiceTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  voiceTagText: {
    fontFamily: 'DM Mono',
    fontSize: 8,
    fontWeight: '500',
    letterSpacing: 1.12,
    color: '#8e8982',
  },
});

export { DetailsView };