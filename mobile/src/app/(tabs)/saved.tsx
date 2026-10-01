import { useMemo, useState, useCallback, useEffect, useRef } from "react";
import {
  View,
  Text,
  Pressable,
  TextInput,
  StyleSheet,
  Modal,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import {
  Plus,
  Search,
  Bookmark,
  Check,
  ChevronDown,
  Headphones,
  Sparkles,
  X,
  ArrowRight,
} from "lucide-react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { memoriesApi } from "@/api/memories";
import type { MemoryResponse } from "@/types/api";

type ViewType = "timeline" | "saved";

type UIData = {
  id: number;
  content: string;
  summary: string | null;
  source: string;
  occurred_at: string | null;
  created_at: string;
  topics: string[] | null;
  entities: string[] | null;
  displayDate: Date;
  dateLabel: string;
  time: string;
  month: string;
  day: string;
  isVoice: boolean;
};

export default function HomeScreen() {
  const router = useRouter();
  const [memories, setMemories] = useState<UIData[]>([]);
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set());
  const [view, setView] = useState<ViewType>("saved");
  const [search, setSearch] = useState("");
  const [isComposerOpen, setIsComposerOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<number | null>(null);

  const mountedRef = useRef(true);

  const mapMemory = (m: MemoryResponse): UIData => {
    const date = m.occurred_at ? new Date(m.occurred_at) : new Date(m.created_at);
    const dateLabel = date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
    });
    const time = date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
    const month = date
      .toLocaleDateString("en-US", { month: "short" })
      .toUpperCase();
    const day = String(date.getDate()).padStart(2, "0");

    return {
      id: m.id,
      content: m.content,
      summary: m.summary,
      source: m.source,
      occurred_at: m.occurred_at,
      created_at: m.created_at,
      topics: m.topics,
      entities: m.entities,
      displayDate: date,
      dateLabel,
      time,
      month,
      day,
      isVoice: m.source === "voice",
    };
  };

  const loadMemories = useCallback(async (isRefresh = false) => {
    if (!isRefresh) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError(null);

    try {
      const data = await memoriesApi.getSaved();
      if (mountedRef.current) {
        const mapped = data.map(mapMemory);
        setMemories(mapped);
      }
    } catch (err) {
      if (mountedRef.current) {
        const message = err instanceof Error ? err.message : "Failed to load saved memories";
        setError(message);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadMemories();

    return () => {
      mountedRef.current = false;
    };
  }, [loadMemories]);

  const onRefresh = () => loadMemories(true);

  const unsaveMemory = useCallback(async (id: number) => {
    if (removingId === id) return;

    setRemovingId(id);

    try {
      await memoriesApi.unsave(id);
      setMemories((current) => current.filter((m) => m.id !== id));
      setSavedIds((current) => {
        const next = new Set(current);
        next.delete(id);
        return next;
      });
    } catch (err) {
      console.error("Failed to unsave memory:", err);
    } finally {
      if (mountedRef.current) {
        setRemovingId(null);
      }
    }
  }, [removingId]);

  const savedMemories = useMemo(
    () => memories.filter((memory) => savedIds.has(memory.id)),
    [memories, savedIds],
  );

  const filteredMemories = useMemo(() => {
    const query = search.trim().toLowerCase();
    const source = view === "timeline" ? memories : savedMemories;
    if (!query) return source;
    return source.filter((memory) =>
      [
        memory.content,
        memory.summary ?? "",
        ...(memory.topics ?? []),
        ...(memory.entities ?? []),
      ].some((field) => field.toLowerCase().includes(query)),
    );
  }, [memories, savedMemories, search, view]);

  const addMemory = useCallback(() => {
    if (!title.trim() || !note.trim()) return;
    const now = new Date();
    const month = now
      .toLocaleDateString("en-US", { month: "short" })
      .toUpperCase();
    const day = String(now.getDate()).padStart(2, "0");
    const dateLabel = now.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
    });
    const time = now.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });

    const newMemory: UIData = {
      id: Date.now(),
      content: note.trim(),
      summary: null,
      source: "text",
      occurred_at: now.toISOString(),
      created_at: now.toISOString(),
      topics: [],
      entities: [],
      displayDate: now,
      dateLabel,
      time,
      month,
      day,
      isVoice: false,
    };

    setMemories((current) => [newMemory, ...current]);
    setTitle("");
    setNote("");
    setIsComposerOpen(false);
  }, [title, note]);

  const switchView = (newView: ViewType) => {
    setView(newView);
    setSearch("");
  };

  const isLastItem = (index: number, total: number) => index === total - 1;

  const renderMemory = (memory: UIData, index: number, total: number) => (
    <Pressable
      style={styles.memoryEntry}
      key={memory.id}
      onPress={() => router.push(`/memory/${memory.id}` as any)}
    >
      <View style={styles.dateColumn}>
        <Text style={styles.dateMonth}>{memory.month}</Text>
        <Text style={styles.dateDay}>{memory.day}</Text>
        {!isLastItem(index, total) && <View style={styles.dateLine} />}
      </View>
      <View style={styles.memoryCard}>
        <View style={styles.memoryMeta}>
          <Text style={styles.memoryMetaText}>{memory.dateLabel}</Text>
          <Text style={styles.metaDot}>·</Text>
          <Text style={styles.memoryMetaText}>{memory.time}</Text>
        </View>
        <Text style={styles.memoryContent} numberOfLines={4}>
          {memory.content}
        </Text>
        {memory.summary && (
          <View style={styles.summaryBox}>
            <View style={styles.summaryLabel}>
              <Sparkles size={12} strokeWidth={1.7} color="#a95c49" />
              <Text style={styles.summaryLabelText}>MEMORY UNDERSTOOD</Text>
            </View>
            <Text style={styles.summaryText}>{memory.summary}</Text>
          </View>
        )}
        <View style={styles.cardFooter}>
          {memory.isVoice && (
            <View style={styles.voiceTag}>
              <Headphones size={13} strokeWidth={1.7} color="#8e8982" />
              <Text style={styles.voiceTagText}>VOICE NOTE</Text>
            </View>
          )}
          <Pressable
            style={[
              { marginLeft: "auto" },
              savedIds.has(memory.id) && styles.saveButtonSaved,
            ]}
            onPress={() => unsaveMemory(memory.id)}
            accessibilityLabel="Unsave memory"
            disabled={removingId === memory.id}
          >
            {savedIds.has(memory.id) ? (
              <Check size={14} strokeWidth={2.2} color="#a95c49" />
            ) : (
              <Bookmark size={14} strokeWidth={1.7} color="#a39b92" />
            )}
          </Pressable>
        </View>
      </View>
    </Pressable>
  );

  const currentCount =
    view === "timeline" ? memories.length : savedMemories.length;
  const eyebrowText = view === "timeline" ? "YOUR ARCHIVE" : "KEPT CLOSE";
  const countLabel = view === "timeline" ? "ENTRIES" : "SAVED";
  const h1Text =
    view === "timeline" ? "A life, remembered." : "Your kept memories.";
  const introCopy =
    view === "timeline"
      ? "A quiet place for the things worth keeping."
      : "A smaller, quieter shelf — the ones you returned to.";
  const timelineHeaderText = view === "timeline" ? "RECENTLY" : "COLLECTION";
  const yearSelectText = view === "timeline" ? "2024" : "All";
  const searchPlaceholder =
    view === "timeline" ? "Search your memories" : "Search saved memories";
  const emptyStateTitle =
    view === "timeline" ? "No memories found." : "Nothing matches your search.";
  const emptyStateSubtitle =
    view === "timeline"
      ? "Try a different word or add a new entry."
      : "Try a different word.";

  if (loading && memories.length === 0) {
    return (
      <SafeAreaView style={styles.phoneFrame} edges={["top"]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#a95c49" />
          <Text style={styles.loadingText}>Loading saved memories...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error && memories.length === 0) {
    return (
      <SafeAreaView style={styles.phoneFrame} edges={["top"]}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Error: {error}</Text>
          <Pressable style={styles.retryButton} onPress={onRefresh}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.phoneFrame} edges={["top"]}>
      <View style={styles.staticContent}>
        <View style={styles.introBlock}>
          <View style={styles.eyebrowRow}>
            <Text style={styles.eyebrow}>{eyebrowText}</Text>
            <Text style={styles.archiveCount}>
              {currentCount} {countLabel}
            </Text>
          </View>
          <Text style={styles.h1}>
            <Text>{h1Text.split(" ").slice(0, -1).join(" ")} </Text>
            <Text style={styles.h1Em}>{h1Text.split(" ").pop()}</Text>
          </Text>
          <Text style={styles.introCopy}>{introCopy}</Text>
        </View>

        <View style={styles.searchWrap}>
          <Search size={17} strokeWidth={1.7} color="#8f8981" />
          <TextInput
            style={styles.searchInput}
            value={search}
            onChangeText={setSearch}
            placeholder={searchPlaceholder}
            placeholderTextColor="#9c968f"
          />
          {search && (
            <Pressable
              style={styles.clearSearch}
              onPress={() => setSearch("")}
              accessibilityLabel="Clear search"
            >
              <X size={14} strokeWidth={1.7} color="#827a73" />
            </Pressable>
          )}
        </View>

        <View style={styles.timelineHeader}>
          <Text style={styles.timelineHeaderText}>{timelineHeaderText}</Text>
          <Pressable style={styles.yearSelect}>
            <Text style={styles.yearSelectText}>{yearSelectText}</Text>
            <ChevronDown size={14} strokeWidth={1.7} color="#716b64" />
          </Pressable>
        </View>
      </View>

      <ScrollView
        style={styles.contentScroll}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {filteredMemories.length > 0 ? (
          <View style={styles.timeline}>
            {filteredMemories.map((memory, index) =>
              renderMemory(memory, index, filteredMemories.length),
            )}
          </View>
        ) : view === "timeline" ? (
          <View style={styles.emptyState}>
            <Search size={20} strokeWidth={1.7} color="#8f8981" />
            <Text style={styles.emptyStateTitle}>{emptyStateTitle}</Text>
            <Text style={styles.emptyStateSubtitle}>{emptyStateSubtitle}</Text>
          </View>
        ) : null}

        {view === "timeline" && (
          <View style={styles.endMark}>
            <View style={styles.endMarkLine} />
            <Text style={styles.endMarkText}>THE PRESENT</Text>
            <View style={styles.endMarkLine} />
          </View>
        )}

        {view === "saved" && savedMemories.length === 0 && (
          <View style={styles.savedEmpty}>
            <View style={styles.savedEmptyIcon}>
              <Bookmark size={26} strokeWidth={1.4} color="#b8b0a6" />
            </View>
            <Text style={styles.savedEmptyTitle}>Nothing kept yet.</Text>
            <Text style={styles.savedEmptyText}>
              Tap the bookmark on any memory to hold it here — a private shelf
              of the moments you want to return to.
            </Text>
            <Pressable
              style={styles.browseButton}
              onPress={() => switchView("timeline")}
            >
              <Text style={styles.browseButtonText}>Browse your timeline</Text>
              <ArrowRight size={15} strokeWidth={1.7} color="#a95c49" />
            </Pressable>
          </View>
        )}

        {view === "saved" && savedMemories.length > 0 && (
          <View style={styles.endMark}>
            <View style={styles.endMarkLine} />
            <Text style={styles.endMarkText}>END OF COLLECTION</Text>
            <View style={styles.endMarkLine} />
          </View>
        )}
      </ScrollView>

  

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  phoneFrame: {
    flex: 1,
    width: "100%",
    backgroundColor: "#f6f3ed",
  },
  statusBar: {
    height: 30,
    paddingTop: 10,
    paddingHorizontal: 24,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  contentContainer: {
    paddingHorizontal: 27,
    paddingBottom: 125,
  },
  statusTime: {
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 0.03,
    color: "#2d2b29",
  },
  statusIcons: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  signal: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 1.5,
    height: 10,
  },
  signalBar: {
    width: 2,
    borderRadius: 2,
    backgroundColor: "#2d2b29",
  },
  wifi: {
    width: 12,
    height: 8,
    borderWidth: 1.5,
    borderColor: "#2d2b29",
    borderBottomWidth: 0,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    transform: [{ scaleX: 1.05 }],
  },
  battery: {
    width: 18,
    height: 9,
    borderWidth: 1,
    borderColor: "#2d2b29",
    borderRadius: 3,
    padding: 1,
  },
  batteryFill: {
    width: "70%",
    height: "100%",
    borderRadius: 1,
    backgroundColor: "#2d2b29",
  },
  contentScroll: {
    flex: 1,
  },
  introBlock: {
    paddingBottom: 24,
  },
  eyebrowRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  eyebrow: {
    fontFamily: "DM Mono",
    fontSize: 9,
    fontWeight: "500",
    letterSpacing: 1.26,
    color: "#a95c49",
  },
  archiveCount: {
    fontFamily: "DM Mono",
    fontSize: 9,
    fontWeight: "400",
    letterSpacing: 1.26,
    color: "#9e978f",
  },
  h1: {
    marginTop: 14,
    marginBottom: 8,
    color: "#292725",
    fontFamily: "Libre Baskerville",
    fontSize: 42,
    fontWeight: "400",
    letterSpacing: -2.31,
    lineHeight: 41.58,
  },
  h1Em: {
    fontFamily: "Libre Baskerville",
    fontStyle: "italic",
    color: "#a95c49",
  },
  introCopy: {
    margin: 0,
    color: "#858079",
    fontSize: 13,
    lineHeight: 19.5,
  },
  searchWrap: {
    height: 43,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 13,
    backgroundColor: "#eeebe4",
    borderWidth: 1,
    borderColor: "rgba(45, 43, 41, 0.1)",
    borderRadius: 11,
  },
  searchInput: {
    flex: 1,
    fontSize: 12,
    color: "#2d2b29",
    fontFamily: "DM Sans",
  },
  clearSearch: {
    padding: 4,
  },
  timelineHeader: {
    marginTop: 31,
    marginBottom: 17,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  timelineHeaderText: {
    color: "#716b64",
    fontFamily: "DM Mono",
    fontSize: 10,
    fontWeight: "400",
    letterSpacing: 1.7,
  },
  yearSelect: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  yearSelectText: {
    color: "#716b64",
    fontFamily: "DM Mono",
    fontSize: 10,
  },
  timeline: {
    gap: 0,
  },
  memoryEntry: {
    flexDirection: "row",
    gap: 13,
  },
  memoryEntryAccent: {},
  dateColumn: {
    width: 42,
    alignItems: "center",
    flexDirection: "column",
    color: "#9d958d",
  },
  dateMonth: {
    fontFamily: "DM Mono",
    fontSize: 8,
    fontWeight: "400",
    letterSpacing: 1.12,
    color: "#9d958d",
    paddingTop: 4,
  },
  dateDay: {
    marginTop: 3,
    fontFamily: "DM Mono",
    fontSize: 25,
    fontWeight: "400",
    letterSpacing: -2,
    lineHeight: 25,
    color: "#4c4843",
  },
  dateLine: {
    width: 1,
    flex: 1,
    marginTop: 12,
    minHeight: 28,
    backgroundColor: "#dbd5cc",
  },
  memoryCard: {
    flex: 1,
    paddingBottom: 28,
    marginBottom: 23,
    borderBottomWidth: 1,
    borderBottomColor: "#ded9d1",
  },
  memoryMeta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-start",
    gap: 7,
    marginBottom: 9,
  },
  memoryMetaText: {
    fontFamily: "DM Mono",
    fontSize: 9,
    letterSpacing: 0.45,
    color: "#9b948c",
  },
  metaDot: {
    color: "#bd7560",
    fontFamily: "DM Mono",
    fontSize: 9,
  },
  staticContent: {
    paddingTop: 27,
    paddingHorizontal: 27,
    paddingBottom: 8,
  },

  memoryContent: {
    marginTop: 9,
    marginBottom: 11,
    color: "#312e2b",
    fontFamily: "Libre Baskerville",
    fontSize: 20,
    fontWeight: "400",
    lineHeight: 26,
    letterSpacing: -0.7,
  },
  summaryBox: {
    marginTop: 15,
    padding: 11,
    paddingBottom: 12,
    paddingHorizontal: 12,
    borderLeftWidth: 2,
    borderLeftColor: "#c48672",
    backgroundColor: "#f0e9e0",
  },
  summaryLabel: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginBottom: 7,
  },
  summaryLabelText: {
    fontFamily: "DM Mono",
    fontSize: 8,
    fontWeight: "500",
    letterSpacing: 1.12,
    color: "#a95c49",
  },
  summaryText: {
    margin: 0,
    color: "#665f58",
    fontSize: 11,
    lineHeight: 15.95,
    fontFamily: "Libre Baskerville",
  },
  cardFooter: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-start",
    gap: 12,
    marginTop: 15,
  },
  voiceTag: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  voiceTagText: {
    fontFamily: "DM Mono",
    fontSize: 8,
    fontWeight: "500",
    letterSpacing: 1.12,
    color: "#8e8982",
  },
  saveButtonSaved: {
    marginLeft: "auto",
  },
  endMark: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 11,
    marginTop: 33,
    color: "#a39c94",
  },
  endMarkLine: {
    width: 24,
    height: 1,
    backgroundColor: "#d3cdc4",
  },
  endMarkText: {
    fontFamily: "DM Mono",
    fontSize: 8,
    fontWeight: "400",
    letterSpacing: 1.12,
    color: "#a39c94",
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: "center",
    textAlign: "center",
  },
  emptyStateTitle: {
    marginTop: 10,
    marginBottom: 4,
    fontFamily: "Libre Baskerville",
    fontSize: 18,
    fontWeight: "400",
    color: "#534d47",
  },
  emptyStateSubtitle: {
    fontSize: 11,
    color: "#8f8981",
  },
  savedEmpty: {
    padding: 44,
    paddingBottom: 20,
    alignItems: "center",
  },
  savedEmptyIcon: {
    width: 60,
    height: 60,
    borderWidth: 1,
    borderColor: "#ddd6cc",
    borderRadius: 30,
    backgroundColor: "#efebe4",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 18,
  },
  savedEmptyTitle: {
    marginBottom: 10,
    fontFamily: "Libre Baskerville",
    fontSize: 21,
    fontWeight: "400",
    letterSpacing: -0.63,
    color: "#4c4843",
  },
  savedEmptyText: {
    marginBottom: 24,
    maxWidth: 250,
    color: "#8a847d",
    fontSize: 12,
    lineHeight: 18.6,
    textAlign: "center",
  },
  browseButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    paddingHorizontal: 17,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: "#c48672",
    borderRadius: 999,
  },
  browseButtonText: {
    fontFamily: "DM Mono",
    fontSize: 11,
    fontWeight: "600",
    color: "#a95c49",
  },
  addMemory: {
    position: "absolute",
    right: 22,
    bottom: 78,
    zIndex: 3,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingLeft: 13,
    backgroundColor: "#a95c49",
    borderRadius: 999,
    boxShadow: "0 9px 22px rgba(125, 65, 49, 0.22)",
    elevation: 8,
  },
  addMemoryText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#fffaf5",
  },
  bottomNav: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: 66,
    paddingHorizontal: 28,
    paddingVertical: 9,
    paddingBottom: 7,
    flexDirection: "row",
    justifyContent: "space-between",
    backgroundColor: "rgba(250, 248, 243, 0.95)",
    borderTopWidth: 1,
    borderTopColor: "rgba(45, 43, 41, 0.1)",
  },
  navItem: {
    flexDirection: "column",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 9,
    paddingVertical: 2,
  },
  navItemActive: {},
  navItemText: {
    fontFamily: "DM Mono",
    fontSize: 8,
    fontWeight: "400",
    letterSpacing: 0.24,
    color: "#a19a91",
  },
  navItemTextActive: {
    color: "#a95c49",
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(43, 38, 34, 0.28)",
    justifyContent: "flex-end",
  },
  composerContainer: {
    flex: 1,
    justifyContent: "flex-end",
  },
  composer: {
    width: "100%",
    paddingHorizontal: 23,
    paddingTop: 22,
    paddingBottom: 25,
    backgroundColor: "#f6f3ed",
    borderTopLeftRadius: 26,
    borderTopRightRadius: 26,
    boxShadow: "0 -16px 45px rgba(43, 38, 34, 0.16)",
    elevation: 10,
  },
  composerTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 18,
  },
  composerEyebrow: {
    fontFamily: "DM Mono",
    fontSize: 9,
    fontWeight: "500",
    letterSpacing: 0.9,
    color: "#a95c49",
  },
  iconButton: {
    width: 34,
    height: 34,
    borderRadius: 17,
    borderWidth: 1,
    borderColor: "rgba(45, 43, 41, 0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  composerTitle: {
    marginBottom: 22,
    fontFamily: "Libre Baskerville",
    fontSize: 25,
    fontWeight: "400",
    lineHeight: 32.5,
    letterSpacing: -1.125,
    color: "#292725",
  },
  composerTitleEm: {
    fontStyle: "italic",
    color: "#a95c49",
  },
  composerField: {
    marginTop: 15,
  },
  composerLabel: {
    marginBottom: 8,
    fontFamily: "DM Mono",
    fontSize: 9,
    fontWeight: "500",
    letterSpacing: 0.9,
    textTransform: "uppercase",
    color: "#8b837a",
  },
  composerInput: {
    width: "100%",
    paddingHorizontal: 13,
    paddingVertical: 12,
    backgroundColor: "#eeebe4",
    borderWidth: 1,
    borderColor: "#dad2c8",
    borderRadius: 8,
    color: "#3d3934",
    fontFamily: "DM Sans",
    fontSize: 12,
  },
  composerTextArea: {
    minHeight: 100,
    textAlignVertical: "top",
  },
  saveMemory: {
    marginTop: 22,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    paddingVertical: 13,
    backgroundColor: "#a95c49",
    borderRadius: 8,
  },
  saveMemoryDisabled: {
    opacity: 0.45,
  },
  saveMemoryText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#fffaf5",
  },
  arrowRightRotate: {
    transform: [{ rotate: "180deg" }],
  },

  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: "#666",
  },
  errorContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  errorText: {
    fontSize: 16,
    color: "#d32f2f",
    textAlign: "center",
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: "#007AFF",
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
});

export { HomeScreen };