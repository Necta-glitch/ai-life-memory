import React from 'react';
import { useRouter } from 'expo-router';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  TextInput,
  StyleSheet,
} from 'react-native';
import {
  ArrowUp,
  CircleHelp,
  Sparkles,
} from 'lucide-react-native';
import { MemoryResponse } from '@/types/api';

type Props = {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmit: () => void;
  canSubmit: boolean;
  answer: string | null;
  sources: MemoryResponse[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
};

export function AskView({
  query,
  onQueryChange,
  onSubmit,
  canSubmit,
  answer,
  sources,
  loading,
  error,
  onRetry,
}: Props) {
  const router = useRouter();
  const suggestions = [
    'What am I working on?',
    'Find a quiet moment',
    'Show recent ideas',
  ];

  const hasAnswer = answer !== null;
  const hasError = error !== null;
  const showResults = hasAnswer || hasError || loading;
  const sourceCount = sources.length;

  return (
    <View style={styles.screen}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.brand}>
          <View style={styles.brandMark}>
            <Sparkles
              size={14}
              color="#fffaf5"
              strokeWidth={1.8}
            />
          </View>

          <Text style={styles.brandText}>
            MEMORY AI
          </Text>
        </View>

        <Pressable
          style={({ pressed }) => [
            styles.helpButton,
            pressed && styles.helpButtonPressed,
          ]}
          accessibilityLabel="About Memory AI"
        >
          <CircleHelp
            size={18}
            color="#8a847d"
            strokeWidth={1.8}
          />
        </Pressable>
      </View>

      {/* Scroll content */}
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Intro */}
        <View style={styles.intro}>
          <Text style={styles.eyebrow}>
            A QUIET CONVERSATION
          </Text>

          <Text style={styles.introTitle}>
            Ask your{' '}
            <Text style={styles.introTitleItalic}>
              archive.
            </Text>
          </Text>

          <Text style={styles.introDescription}>
            Find connections, patterns, and the moments
            you almost forgot.
          </Text>
        </View>

        {/* Suggestions */}
        {!showResults && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.suggestions}
          >
            {suggestions.map((suggestion) => (
              <Pressable
                key={suggestion}
                style={({ pressed }) => [
                  styles.suggestion,
                  pressed && styles.suggestionPressed,
                ]}
                onPress={() => onQueryChange(suggestion)}
              >
                <Text style={styles.suggestionText}>
                  {suggestion}
                </Text>
              </Pressable>
            ))}
          </ScrollView>
        )}

        {/* Answer Section */}
        {showResults && (
          <View style={styles.answer}>
            <View style={styles.questionBubble}>
              <Text style={styles.questionText}>
                {query}
              </Text>
            </View>

            {loading && (
              <View style={styles.loadingContainer}>
                <Text style={styles.loadingText}>Thinking...</Text>
              </View>
            )}

            {hasError && (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>
                  {error}
                </Text>
                <Pressable style={styles.retryButton} onPress={onRetry}>
                  <Text style={styles.retryButtonText}>Retry</Text>
                </Pressable>
              </View>
            )}

            {hasAnswer && (
              <>
                {sourceCount > 0 && (
                  <Text style={styles.sourceNote}>
                    {sourceCount} relevant memor{sourceCount === 1 ? 'y' : 'ies'} found
                    <Text style={styles.sourceDot}> · </Text>
                    YOUR ARCHIVE
                  </Text>
                )}

                <Text style={styles.answerText}>
                  {answer}
                </Text>

                {sourceCount > 0 && (
                  <View style={styles.citations}>
                    {sources.map((source, _index) => (
                      <Pressable
                        key={source.id}
                        style={styles.citation}
                        onPress={() => router.push(`/memory/${source.id}` as any)}
                      >
                        <Text style={styles.citationText}>
                          {source.summary || 'Memory'}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                )}
              </>
            )}
          </View>
        )}

        {/* Composer */}
        <View style={styles.composer}>
          <TextInput
            value={query}
            onChangeText={onQueryChange}
            placeholder={hasAnswer ? "Ask a follow-up question" : "Ask anything about your memories"}
            placeholderTextColor="#9c968f"
            style={styles.input}
            accessibilityLabel="Ask a follow-up question"
            returnKeyType="send"
            onSubmitEditing={() => {
              if (canSubmit) {
                onSubmit();
              }
            }}
          />

          <Pressable
            style={({ pressed }) => [
              styles.sendButton,
              !canSubmit && styles.sendButtonDisabled,
              pressed &&
                canSubmit &&
                styles.sendButtonPressed,
            ]}
            onPress={onSubmit}
            disabled={!canSubmit}
            accessibilityLabel="Send question"
          >
            <ArrowUp
              size={17}
              color="#fffaf5"
              strokeWidth={2}
            />
          </Pressable>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#f6f3ed',
  },

  // Header
  header: {
    height: 62,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 22,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(45, 43, 41, 0.08)',
  },

  brand: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },

  brandMark: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    backgroundColor: '#a95c49',
  },

  brandText: {
    color: '#2d2b29',
    fontFamily: 'DM Mono',
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1.8,
  },

  helpButton: {
    width: 33,
    height: 33,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(45, 43, 41, 0.14)',
    borderRadius: 17,
  },

  helpButtonPressed: {
    backgroundColor: '#ebe6dd',
  },

  // Scroll
  scroll: {
    flex: 1,
  },

  scrollContent: {
    paddingTop: 27,
    paddingHorizontal: 22,
    paddingBottom: 115,
  },

  // Intro
  intro: {
    paddingBottom: 22,
  },

  eyebrow: {
    color: '#a95c49',
    fontFamily: 'DM Mono',
    fontSize: 9,
    fontWeight: '500',
    letterSpacing: 1.4,
  },

  introTitle: {
    marginTop: 14,
    marginBottom: 9,
    color: '#312e2b',
    fontFamily: 'Libre Baskerville',
    fontSize: 40,
    fontWeight: '400',
    lineHeight: 46,
    letterSpacing: -1.5,
  },

  introTitleItalic: {
    fontStyle: 'italic',
  },

  introDescription: {
    maxWidth: 290,
    color: '#858079',
    fontSize: 13,
    lineHeight: 20,
  },

  // Suggestions
  suggestions: {
    gap: 7,
    paddingHorizontal: 2,
    paddingVertical: 2,
    marginBottom: 27,
  },

  suggestion: {
    paddingVertical: 9,
    paddingHorizontal: 11,
    borderWidth: 1,
    borderColor: '#dcd5cb',
    borderRadius: 999,
    backgroundColor: '#eeebe4',
  },

  suggestionPressed: {
    borderColor: '#c48672',
    backgroundColor: '#f0e9e0',
  },

  suggestionText: {
    color: '#716b64',
    fontSize: 10,
    lineHeight: 13,
  },

  // Answer
  answer: {
    paddingTop: 19,
    paddingBottom: 22,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderTopColor: '#dbd5cc',
    borderBottomColor: '#dbd5cc',
  },

  questionBubble: {
    alignSelf: 'flex-start',
    maxWidth: '94%',
    paddingVertical: 11,
    paddingHorizontal: 13,
    borderTopLeftRadius: 11,
    borderTopRightRadius: 11,
    borderBottomLeftRadius: 11,
    borderBottomRightRadius: 3,
    backgroundColor: '#e7ded2',
  },

  questionText: {
    color: '#4c4843',
    fontSize: 12,
    lineHeight: 17,
  },

  sourceNote: {
    marginTop: 17,
    marginBottom: 13,
    color: '#9e978f',
    fontFamily: 'DM Mono',
    fontSize: 8,
    letterSpacing: 0.5,
  },

  sourceDot: {
    color: '#bd7560',
  },

  loadingContainer: {
    paddingVertical: 20,
    alignItems: 'center',
  },

  loadingText: {
    color: '#858079',
    fontSize: 13,
    fontStyle: 'italic',
  },

  errorContainer: {
    paddingVertical: 20,
    alignItems: 'center',
    gap: 12,
  },

  errorText: {
    color: '#d32f2f',
    fontSize: 13,
    textAlign: 'center',
  },

  retryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#a95c49',
    borderRadius: 8,
  },

  retryButtonText: {
    color: '#fffaf5',
    fontSize: 12,
    fontWeight: '600',
  },

  answerText: {
    marginBottom: 19,
    color: '#69645e',
    fontSize: 13,
    lineHeight: 21,
  },

  answerHeading: {
    marginTop: 3,
    marginBottom: 10,
    color: '#312e2b',
    fontFamily: 'Libre Baskerville',
    fontSize: 19,
    fontWeight: '400',
    lineHeight: 25,
    letterSpacing: -0.6,
  },

  // Citations
  citations: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
  },

  citation: {
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: '#d2a294',
    borderRadius: 3,
  },

  citationText: {
    color: '#8f4f3d',
    fontFamily: 'DM Mono',
    fontSize: 8,
    letterSpacing: 0.5,
  },

  // Composer
  composer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 22,
    paddingTop: 8,
    paddingRight: 8,
    paddingBottom: 8,
    paddingLeft: 14,
    borderWidth: 1,
    borderColor: '#d9d1c7',
    borderRadius: 12,
    backgroundColor: '#eeebe4',
  },

  input: {
    flex: 1,
    minWidth: 0,
    paddingVertical: 4,
    color: '#3d3934',
    fontSize: 12,
  },

  sendButton: {
    width: 31,
    height: 31,
    flexShrink: 0,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
    backgroundColor: '#a95c49',
  },

  sendButtonPressed: {
    backgroundColor: '#914a39',
  },

  sendButtonDisabled: {
    opacity: 0.35,
  },
});