# AI Life Memory — Mobile App Overview

## 1. App Description

AI Life Memory is a personal memory system that allows users to capture, organize, and retrieve personal memories using AI. The app solves the problem of information loss by providing a private, chronological archive where users can save experiences, thoughts, learnings, and events. The core flow is: Capture → Process → Store → Retrieve → Answer. Users add memories via text (and planned voice), the backend processes them with AI-generated summaries and embeddings, and users can later search and ask questions about their past using natural language.

## 2. Mobile Stack

| Technology | Version | Purpose |
|---|---|---|
| React Native | 0.86.3 | Core mobile framework |
| Expo | ~57.0.23 | Development platform and build tools |
| Expo Router | ~57.0.21 | File-based navigation and routing |
| TypeScript | ~6.0.3 | Static type checking |
| React | 19.2.3 | UI library |
| Axios | ^1.20.0 | HTTP client for backend API |
| @react-native-async-storage/async-storage | 2.2.0 | Local persistence (onboarding state) |
| lucide-react-native | ^1.46.0 | Icon library |
| expo-font | ~57.0.4 | Custom font loading |
| expo-image | ~57.0.5 | Image component |
| expo-symbols | ~57.0.3 | SF Symbols support |
| expo-glass-effect | ~57.0.3 | Glass morphism UI effects |
| expo-status-bar | ~57.0.1 | Status bar management |
| expo-splash-screen | ~57.0.9 | Splash screen |
| expo-linking | ~57.0.10 | Deep linking |
| expo-web-browser | ~57.0.3 | Web browser integration |
| react-native-gesture-handler | ~2.32.0 | Gesture handling |
| react-native-reanimated | 4.5.1 | Animations |
| react-native-safe-area-context | ~5.7.0 | Safe area insets |
| react-native-screens | ~4.26.0 | Native screen management |
| react-native-svg | 15.15.4 | SVG support |
| react-native-web | ~0.21.0 | Web compatibility |
| Jest | ^29.7.0 | Unit testing |
| ESLint | ^8.57.0 | Linting |

## 3. Architecture

The app follows a file-based routing architecture using **Expo Router** with a tab-based layout:

```
src/
├── app/
│   ├── _layout.tsx              # Root layout with MemoriesProvider and Tabs
│   ├── index.tsx                # Entry gate: onboarding → login → tabs
│   ├── onboarding/index.tsx     # 4-slide onboarding flow
│   ├── login/index.tsx          # Sign in / sign up screen
│   ├── create-memory.tsx        # Create new memory (standalone route)
│   └── (tabs)/
│       ├── index.tsx            # Memory timeline tab
│       └── saved.tsx            # Saved memories tab
├── api/
│   ├── client.ts                # Axios instance with platform-specific base URL
│   ├── memories.ts              # Memory CRUD + save/unsave endpoints
│   ├── search.ts                # Semantic, keyword, hybrid, rerank, chat
│   ├── chat.ts                  # RAG chat endpoint
│   └── voice.ts                 # Voice memory upload (multipart)
├── context/
│   └── MemoriesContext.tsx      # Global memory state (legacy mock data)
├── components/
│   ├── TabBar.tsx               # Custom bottom tab bar
│   └── MemoryItem.tsx           # Reusable memory display component
├── constants/
│   ├── api.ts                   # API base URL and endpoints
│   └── storage.ts               # AsyncStorage keys
├── lib/
│   └── session.ts               # In-memory auth flag
└── types/
    └── api.ts                   # TypeScript types matching backend schemas
```

**Navigation**: Expo Router with two tabs (Memory, Saved) wrapped in `MemoriesProvider`. The entry screen (`index.tsx`) gates access: checks `AsyncStorage` for onboarding completion → redirects to `/onboarding` or `/login` → then to `/(tabs)`.

**Providers**: `MemoriesProvider` exposes `memories`, `savedIds`, `savedMemories`, `addMemory`, `toggleSaved` via context (currently uses mock data; screens use API directly).

**Backend Communication**: Axios client (`api/client.ts`) with `X-User-ID: dev-user` header. Base URL from `EXPO_PUBLIC_API_URL` env var with platform fallbacks (iOS: `localhost`, Android: `10.0.2.2`, Web: `localhost`).

## 4. Core Features

| Feature | Status | Description |
|---|---|---|
| Onboarding | Implemented | 4-slide flow with AsyncStorage persistence |
| Authentication (Login/Signup) | Implemented | UI complete; mock auth via `setAuthenticated()` |
| Memory Timeline | Implemented | Fetches `/memories/`, displays chronologically with date column, search, pull-to-refresh |
| Saved Memories | Implemented | Separate tab; fetches `/memories/saved`; unsave action |
| Create Memory (Text) | Implemented | Modal composer (title + note) → POST `/memories/` |
| Save/Unsave Memory | Implemented | POST/DELETE `/memories/{id}/save` with optimistic UI |
| Voice Memory API | Implemented (API only) | `voiceApi.create()` uploads audio via multipart to `/memories/voice` |
| Search API | Implemented (API only) | Semantic, keyword, hybrid, rerank endpoints defined |
| RAG Chat API | Implemented (API only) | `/search/chat` returns grounded answer + sources |
| In-app Search UI | Not implemented | Search input exists but only filters local list client-side |
| AI Summaries Display | Implemented | Shows `summary` field from backend in memory cards |

## 5. Memory Model

The mobile `MemoryResponse` type (`src/types/api.ts`) matches the backend schema exactly:

| Field | Type | Description |
|---|---|---|
| `id` | number | Primary key |
| `user_id` | string | Owner identifier |
| `content` | string | Full memory text |
| `summary` | string \| null | AI-generated summary |
| `topics` | string[] \| null | Extracted topics |
| `entities` | string[] \| null | Extracted entities |
| `source` | string | `"text"` or `"voice"` |
| `created_at` | string (ISO) | Server creation timestamp |
| `occurred_at` | string \| null | User-specified event time |

The UI maps this to a display format (`UIData` in screens) adding computed fields: `displayDate`, `dateLabel`, `time`, `month`, `day`, `isVoice`.

## 6. Screens and Navigation

| Route | Purpose | Tab |
|---|---|---|
| `/` | Entry gate: checks onboarding → redirects | — |
| `/onboarding` | 4-slide intro; marks completion in AsyncStorage | — |
| `/login` | Sign in / sign up (mock auth) | — |
| `/(tabs)` | Tab container (Memory, Saved) | — |
| `/(tabs)/index` | Main timeline: all memories, search, composer | Memory |
| `/(tabs)/saved` | Saved memories only, toggle timeline/saved view | Saved |
| `/create-memory` | Standalone create screen (legacy, not used in tabs) | — |

Tab bar: Custom `TabBar.tsx` with `Clock3` (Memory) and `Bookmark` (Saved) icons, floating pill design.

## 7. Backend Integration

**API Client**: `src/api/client.ts` — Axios instance with:
- Base URL: `EXPO_PUBLIC_API_URL` or platform fallback
- 30s timeout
- `X-User-ID: dev-user` header on all requests
- Response interceptors for 401/404/500 handling

**Endpoints Consumed by Mobile**:

| Endpoint | Method | Used By |
|---|---|---|
| `/memories/` | GET | Timeline, Saved (via `/memories/saved`) |
| `/memories/` | POST | Create memory (text) |
| `/memories/{id}` | GET | Not yet used |
| `/memories/{id}` | PUT | Not yet used |
| `/memories/{id}` | DELETE | Not yet used |
| `/memories/saved` | GET | Saved tab |
| `/memories/{id}/save` | POST | Save button (both tabs) |
| `/memories/{id}/save` | DELETE | Unsave button |
| `/memories/voice` | POST | Voice API (not wired in UI) |
| `/search/semantic` | POST | Not yet used in UI |
| `/search/keyword` | POST | Not yet used in UI |
| `/search/hybrid` | POST | Not yet used in UI |
| `/search/rerank` | POST | Not yet used in UI |
| `/search/chat` | POST | Not yet used in UI |

**Models**: `src/types/api.ts` mirrors backend Pydantic schemas (`MemoryResponse`, `MemoryCreate`, `MemoryUpdate`, `SaveMemoryResponse`, search/rag types).

## 8. State Management

| Mechanism | Scope | Purpose |
|---|---|---|
| `MemoriesContext` | Global (legacy) | Mock memory data, savedIds, add/toggle — **not used by tab screens** |
| `useState` / `useReducer` | Screen-local | Timeline/saved screens manage their own `memories`, `savedIds`, `search`, `loading`, `error` |
| `AsyncStorage` | Persistent | `onboarding_completed` flag only |
| `session.ts` (in-memory) | App session | `authenticated` boolean flag (mock) |

**Note**: The tab screens (`index.tsx`, `saved.tsx`) bypass `MemoriesContext` and call `memoriesApi` directly. `MemoriesContext` appears to be legacy code from a mock-data phase.

## 9. UI / Design

**Visual Language**:
- Background: `#f6f3ed` (warm off-white)
- Accent: `#a95c49` (terracotta)
- Text primary: `#292725`, secondary: `#858079`, muted: `#a19a91`
- Border/divider: `#dbd5cc`, `#ded9d1`

**Typography**:
- Display/Headlines: `Libre Baskerville` (serif, italic for emphasis)
- UI labels/meta: `DM Mono` (monospace, tight letter-spacing)
- Body/inputs: `DM Sans`

**Components**:
- **Timeline**: Left date column (month/day) with connecting line, right memory cards with content, optional summary box, voice tag, save button
- **Memory Card**: Border-bottom separator, meta row (date·time), truncated content (4 lines), summary in accent box, footer with voice tag + bookmark/check icon
- **Composer Modal**: Slide-up from bottom, title + note fields, disabled save until both filled
- **Search Bar**: Rounded pill with icon, clear button
- **Bottom Tab Bar**: Floating pill with two icons, active state fills background with accent color
- **Empty States**: Illustrated with search icon, descriptive copy, CTA button (saved tab)

## 10. Development Status

### Implemented
- Onboarding flow with persistence
- Login/Signup UI (mock authentication)
- Memory timeline with server data
- Saved memories tab with server data
- Create memory via modal composer (text only)
- Save/unsave with optimistic updates
- Client-side search filtering
- Pull-to-refresh on both tabs
- Custom tab bar and navigation structure
- Voice memory API (upload endpoint)
- Search & RAG API clients (semantic, keyword, hybrid, rerank, chat)
- TypeScript types aligned with backend

### In Progress
- Voice memory UI integration (recording/upload in composer)
- Real authentication (JWT, token storage, interceptors)
- In-app semantic/hybrid search UI (currently only client-side filter)

### Planned
- RAG chat interface (ask questions about memories)
- Search screens with backend-powered results
- Offline support / sync
- Image/document memory support
- Export/backup functionality

## 11. Important Development Notes

- **Two data sources**: `MemoriesContext` (mock) vs direct API calls in screens. Screens are the source of truth.
- **Auth is mocked**: `X-User-ID: dev-user` header; `session.ts` only tracks boolean. Replace with real JWT when backend auth ready.
- **Platform-specific API URL**: Android emulator needs `10.0.2.2`, iOS simulator uses `localhost`. Configured in `client.ts`.
- **Composer is a modal** in both tabs, not a separate route. `/create-memory` exists but is unused.
- **Saved tab has dual view**: "Timeline" (all memories) and "Saved" (filtered). Toggle via segmented control (not yet visible in code — `view` state exists).
- **Search is client-side only**: The search input filters `memories` array locally. Backend search endpoints exist but not wired.
- **Fonts**: `Libre Baskerville`, `DM Sans`, `DM Mono` loaded via `expo-font` (verify `app/_layout.tsx` or root for `useFonts`).
- **Key files to modify for new features**:
  - Add API endpoints → `src/api/*.ts` + `src/types/api.ts`
  - New screens → `src/app/` (Expo Router auto-generates routes)
  - Shared UI → `src/components/`
  - Global state → consider replacing `MemoriesContext` with a proper solution (Zustand, React Query, or Context + API)
- **No test files found** for mobile; `jest-expo` configured but no tests written.