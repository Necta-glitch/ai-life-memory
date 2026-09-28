import { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';

type Memory = {
  id: number;
  month: string;
  day: string;
  dateLabel: string;
  time: string;
  title: string;
  note: string;
  summary: string;
  category: string;
  hasVoice?: boolean;
  accent?: boolean;
};

type MemoriesContextType = {
  memories: Memory[];
  savedIds: Set<number>;
  savedMemories: Memory[];
  addMemory: (memory: Omit<Memory, 'id'>) => void;
  toggleSaved: (id: number) => void;
};

const initialMemories: Memory[] = [
  {
    id: 1,
    month: 'SEP',
    day: '10',
    dateLabel: 'September 10',
    time: '09:42 AM',
    title: 'Built my first RRF search pipeline',
    note: 'Finally got reciprocal rank fusion working across the keyword and semantic indexes. The results feel noticeably more human.',
    summary: 'You combined two search strategies into one ranking system and saw a meaningful improvement in relevance.',
    category: 'WORK',
    hasVoice: true,
    accent: true,
  },
  {
    id: 2,
    month: 'SEP',
    day: '08',
    dateLabel: 'September 8',
    time: '07:18 PM',
    title: 'Discovered semantic search',
    note: 'The first time I searched for "quiet places to read" and actually found the notes about the little library in Kyoto.',
    summary: 'A new way of searching made an old travel note feel useful again.',
    category: 'LEARNING',
  },
  {
    id: 3,
    month: 'SEP',
    day: '03',
    dateLabel: 'September 3',
    time: '06:35 AM',
    title: 'Started learning embeddings',
    note: 'Coffee, a blank notebook, and the feeling that I am finally beginning to understand the shape of this thing.',
    summary: 'You began a new technical chapter with a quiet morning study session.',
    category: 'IDEAS',
    hasVoice: true,
  },
  {
    id: 4,
    month: 'AUG',
    day: '28',
    dateLabel: 'August 28',
    time: '04:10 PM',
    title: 'Coffee with a friend',
    note: 'We talked for three hours without noticing. She reminded me that the best ideas usually arrive sideways.',
    summary: 'An unhurried conversation brought a fresh perspective to a week of intense work.',
    category: 'PEOPLE',
  },
];

const MemoriesContext = createContext<MemoriesContextType | undefined>(undefined);

export function MemoriesProvider({ children }: { children: ReactNode }) {
  const [memories, setMemories] = useState<Memory[]>(initialMemories);
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set([1, 3]));

  const addMemory = useCallback((memory: Omit<Memory, 'id'>) => {
    setMemories((current) => [
      { ...memory, id: Date.now() },
      ...current,
    ]);
  }, []);

  const toggleSaved = useCallback((id: number) => {
    setSavedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const savedMemories = useMemo(
    () => memories.filter((memory) => savedIds.has(memory.id)),
    [memories, savedIds],
  );

  return (
    <MemoriesContext.Provider value={{ memories, savedIds, savedMemories, addMemory, toggleSaved }}>
      {children}
    </MemoriesContext.Provider>
  );
}

export function useMemories() {
  const context = useContext(MemoriesContext);
  if (!context) {
    throw new Error('useMemories must be used within a MemoriesProvider');
  }
  return context;
}