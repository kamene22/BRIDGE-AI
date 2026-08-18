import { VoiceLounge } from './VoiceLounge';
import { ChatPanel } from './ChatPanel';
import { useAppStore } from '../store/appStore';
import { MessageCircle, Mic, RotateCcw } from 'lucide-react';
import { useState } from 'react';
import './AppShell.css';

type ActiveTab = 'voice' | 'chat';

export function AppShell() {
  const resetSession = useAppStore((s) => s.resetSession);
  const sessionId = useAppStore((s) => s.sessionId);
  const [activeTab, setActiveTab] = useState<ActiveTab>('voice');

  return (
    <div className="app-shell">
      {/* ── Header ────────────────────────────────── */}
      <header className="app-header">
        <div className="app-brand">
          <div className="app-logo">
            <span className="logo-letter">A</span>
          </div>
          <div className="app-brand-text">
            <h1 className="app-name">Bridge AI</h1>
            <span className="app-tagline">Amani Career Mentor</span>
          </div>
        </div>

        {/* Mobile tab switcher */}
        <div className="app-tabs-mobile">
          <button
            className={`tab-btn ${activeTab === 'voice' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('voice')}
          >
            <Mic size={16} />
            Voice
          </button>
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'tab-active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageCircle size={16} />
            Chat
          </button>
        </div>

        <div className="app-actions">
          <span className="session-id">
            {sessionId.slice(0, 16)}
          </span>
          <button
            className="reset-btn"
            onClick={resetSession}
            aria-label="Reset session"
            title="New session"
          >
            <RotateCcw size={16} />
          </button>
        </div>
      </header>

      {/* ── Main Content ──────────────────────────── */}
      <main className="app-main">
        <div className={`app-voice-pane ${activeTab === 'voice' ? 'pane-visible' : ''}`}>
          <VoiceLounge />
        </div>
        <div className={`app-chat-pane ${activeTab === 'chat' ? 'pane-visible' : ''}`}>
          <ChatPanel />
        </div>
      </main>
    </div>
  );
}
