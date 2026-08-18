import { create } from 'zustand';

// ── Types ───────────────────────────────────────────────

export type OrbState = 'idle' | 'listening' | 'speaking' | 'thinking';

export type LanguagePreference = 'adaptive' | 'english' | 'kiswahili' | 'sheng';

export interface Message {
  id: string;
  role: 'user' | 'amani' | 'system';
  text: string;
  timestamp: number;
  guardrails?: {
    scam_detected?: boolean;
    legal_boundary_triggered?: boolean;
    out_of_scope?: boolean;
  };
  sources?: string[];
  isStreaming?: boolean;
}

// ── Store Interface ─────────────────────────────────────

interface AppState {
  // Session
  sessionId: string;

  // Connection
  connected: boolean;
  orbState: OrbState;
  voiceEnabled: boolean;

  // Audio amplitude (0.0–1.0), driven by AudioEngine via useRef (not re-rendering)
  micAmplitude: number;
  speakerAmplitude: number;

  // Messages (shared between text chat and voice transcripts)
  messages: Message[];

  // Live subtitles (voice mode)
  userSubtitle: string;
  amaniSubtitle: string;

  // Voice & Preferences
  voiceName: string;
  languagePreference: LanguagePreference;

  // Actions — UI
  setOrbState: (state: OrbState) => void;
  setVoiceEnabled: (enabled: boolean) => void;
  setConnected: (connected: boolean) => void;
  setVoiceName: (name: string) => void;
  setLanguagePreference: (pref: LanguagePreference) => void;

  // Actions — Messages
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  updateLastAmaniMessage: (text: string) => void;
  commitAmaniMessage: (guardrails?: Message['guardrails'], sources?: string[]) => void;

  // Actions — Subtitles
  setUserSubtitle: (text: string) => void;
  setAmaniSubtitle: (text: string) => void;
  commitUserSubtitle: () => void;

  // Actions — Amplitude
  setMicAmplitude: (v: number) => void;
  setSpeakerAmplitude: (v: number) => void;

  // Actions — Text chat
  sendTextMessage: (text: string) => Promise<void>;

  // Reset
  resetSession: () => void;
}

// ── Helpers ─────────────────────────────────────────────

function generateId(): string {
  return Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

function generateSessionId(): string {
  return 'session_' + generateId();
}

// ── Store ───────────────────────────────────────────────

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  sessionId: generateSessionId(),
  connected: false,
  orbState: 'idle',
  voiceEnabled: false,
  micAmplitude: 0,
  speakerAmplitude: 0,
  messages: [],
  userSubtitle: '',
  amaniSubtitle: '',
  voiceName: 'Kore',
  languagePreference: 'adaptive',

  // ── UI Actions ──────────────────────────────────────

  setOrbState: (orbState) => set({ orbState }),
  setVoiceEnabled: (voiceEnabled) => set({ voiceEnabled }),
  setConnected: (connected) => set({ connected }),
  setVoiceName: (voiceName) => set({ voiceName }),
  setLanguagePreference: (languagePreference) => set({ languagePreference }),

  // ── Message Actions ─────────────────────────────────

  addMessage: (msg) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...msg, id: generateId(), timestamp: Date.now() },
      ],
    })),

  updateLastAmaniMessage: (text) =>
    set((state) => {
      const msgs = [...state.messages];
      const lastAmani = msgs.findLast((m) => m.role === 'amani' && m.isStreaming);
      if (lastAmani) {
        lastAmani.text += text;
      } else {
        msgs.push({
          id: generateId(),
          role: 'amani',
          text,
          timestamp: Date.now(),
          isStreaming: true,
        });
      }
      return { messages: msgs };
    }),

  commitAmaniMessage: (guardrails, sources) =>
    set((state) => {
      const msgs = [...state.messages];
      const lastAmani = msgs.findLast((m) => m.role === 'amani' && m.isStreaming);
      if (lastAmani) {
        lastAmani.isStreaming = false;
        if (guardrails) lastAmani.guardrails = guardrails;
        if (sources) lastAmani.sources = sources;
      }
      return { messages: msgs };
    }),

  // ── Subtitle Actions ────────────────────────────────

  setUserSubtitle: (userSubtitle) => set({ userSubtitle }),
  setAmaniSubtitle: (amaniSubtitle) => set({ amaniSubtitle }),

  commitUserSubtitle: () => {
    const { userSubtitle } = get();
    if (userSubtitle.trim()) {
      get().addMessage({ role: 'user', text: userSubtitle.trim() });
      set({ userSubtitle: '' });
    }
  },

  // ── Amplitude Actions ───────────────────────────────

  setMicAmplitude: (micAmplitude) => set({ micAmplitude }),
  setSpeakerAmplitude: (speakerAmplitude) => set({ speakerAmplitude }),

  // ── Text Chat ───────────────────────────────────────

  sendTextMessage: async (text: string) => {
    const { sessionId, addMessage } = get();

    addMessage({ role: 'user', text });

    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://bridge-ai-backend-91js.onrender.com';

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();

      addMessage({
        role: 'amani',
        text: data.answer,
        guardrails: data.guardrails,
        sources: data.sources,
      });
    } catch (err) {
      console.error('Text chat error:', err);
      addMessage({
        role: 'system',
        text: 'Connection error — please try again.',
      });
    }
  },

  // ── Reset ───────────────────────────────────────────

  resetSession: () =>
    set({
      sessionId: generateSessionId(),
      connected: false,
      orbState: 'idle',
      voiceEnabled: false,
      messages: [],
      userSubtitle: '',
      amaniSubtitle: '',
    }),
}));
