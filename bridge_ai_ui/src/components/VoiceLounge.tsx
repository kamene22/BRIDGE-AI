import { useState } from 'react';
import { useAppStore, type LanguagePreference } from '../store/appStore';
import { useVoiceSession } from '../hooks/useVoiceSession';
import { LuminousOrb } from './LuminousOrb';
import { SubtitleOverlay } from './SubtitleOverlay';
import { Mic, MicOff, Phone, PhoneOff, Settings, Sparkles, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import './VoiceLounge.css';

const STARTER_PROMPTS = [
  "I just got my first job",
  "I don't think I'm doing well",
  "I'm feeling overwhelmed",
  "I'm struggling with my manager",
  "I don't know what to do next",
  "Help me think this through"
];

const VOICES = ['Kore', 'Puck', 'Charon', 'Fenrir', 'Aoede', 'Zephyr'];

const LANGUAGES: { id: LanguagePreference; label: string }[] = [
  { id: 'adaptive', label: 'Adaptive (Natural)' },
  { id: 'english', label: 'English' },
  { id: 'kiswahili', label: 'Kiswahili' },
  { id: 'sheng', label: 'Sheng' },
];

export function VoiceLounge() {
  const orbState = useAppStore((s) => s.orbState);
  const connected = useAppStore((s) => s.connected);
  const voiceEnabled = useAppStore((s) => s.voiceEnabled);
  const voiceName = useAppStore((s) => s.voiceName);
  const setVoiceName = useAppStore((s) => s.setVoiceName);
  const languagePreference = useAppStore((s) => s.languagePreference);
  const setLanguagePreference = useAppStore((s) => s.setLanguagePreference);
  const messages = useAppStore((s) => s.messages);

  const { connectVoice, disconnectVoice, toggleMic, sendPrompt } = useVoiceSession();
  const [showSettings, setShowSettings] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);

  const handleConnect = () => {
    if (connected) {
      disconnectVoice();
    } else {
      connectVoice();
    }
  };

  const handlePromptClick = (text: string) => {
    sendPrompt(text);
  };

  // Only show starter prompt chips if not connected and history has few messages
  const userMessages = messages.filter((m) => m.role === 'user');
  const showStarterPrompts = !connected && userMessages.length < 2;

  return (
    <div className="voice-lounge">
      {/* Calm Ambient Background */}
      <div className="voice-bg" data-state={orbState} />

      {/* Main Content Area */}
      <div className="voice-content">
        {/* Top Navigation & Preference Bar */}
        <div className="voice-header-bar">
          <div className="voice-greeting-header">
            <span className="greeting-sub">Bridge AI Companion</span>
            <h2 className="greeting-title">
              "Hey there, I'm Amani. Think of me as your sounding board for anything workplace or career-related."
            </h2>
          </div>

          <button
            className={`settings-toggle-btn ${showSettings ? 'active' : ''}`}
            onClick={() => setShowSettings(!showSettings)}
            aria-label="Communication Preferences"
          >
            <Settings size={18} />
            <span className="settings-btn-label">Preferences</span>
          </button>
        </div>

        {/* Expandable Preferences Controls */}
        {showSettings && (
          <div className="preferences-panel">
            <div className="pref-group">
              <label className="pref-label">Language Register</label>
              <div className="pref-pills">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.id}
                    className={`pref-pill ${lang.id === languagePreference ? 'pref-pill-active' : ''}`}
                    onClick={() => setLanguagePreference(lang.id)}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="pref-group">
              <label className="pref-label">Voice Tone</label>
              <div className="pref-pills">
                {VOICES.map((v) => (
                  <button
                    key={v}
                    className={`pref-pill ${v === voiceName ? 'pref-pill-active' : ''}`}
                    onClick={() => setVoiceName(v)}
                    disabled={connected}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Center Orb Stage */}
        <div className="voice-orb-stage">
          <LuminousOrb size={220} />
        </div>

        {/* Subtitle Overlay */}
        <SubtitleOverlay />

        {/* Floating Starter Prompts */}
        {showStarterPrompts && (
          <div className="floating-prompts-container">
            <div className="prompts-header">
              <Sparkles size={14} className="sparkle-icon" />
              <span>Conversation starters</span>
            </div>
            <div className="prompts-grid">
              {STARTER_PROMPTS.map((promptText, idx) => (
                <button
                  key={idx}
                  className="prompt-chip"
                  onClick={() => handlePromptClick(promptText)}
                >
                  {promptText}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Conversation Continuity Transcript Drawer */}
        {messages.length > 0 && (
          <div className="transcript-drawer">
            <button
              className="transcript-toggle-btn"
              onClick={() => setShowTranscript(!showTranscript)}
            >
              <MessageSquare size={16} />
              <span>Recent Dialogue ({messages.length})</span>
              {showTranscript ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
            </button>

            {showTranscript && (
              <div className="transcript-history-list">
                {messages.map((m) => (
                  <div key={m.id} className={`transcript-bubble ${m.role}`}>
                    <span className="bubble-speaker">{m.role === 'user' ? 'You' : m.role === 'amani' ? 'Amani' : 'System'}</span>
                    <p className="bubble-text">{m.text}</p>
                    {m.sources && m.sources.length > 0 && (
                      <span className="bubble-source">Grounded: {m.sources.join(', ')}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Bottom Control Bar */}
        <div className="voice-controls-bar">
          <button
            className={`control-btn mic-btn ${voiceEnabled ? 'mic-active' : ''}`}
            onClick={toggleMic}
            disabled={!connected}
            aria-label={voiceEnabled ? 'Mute microphone' : 'Unmute microphone'}
          >
            {voiceEnabled ? <Mic size={22} /> : <MicOff size={22} />}
          </button>

          <button
            className={`control-btn call-btn ${connected ? 'call-end' : ''}`}
            onClick={handleConnect}
            aria-label={connected ? 'End voice session' : 'Start voice session'}
          >
            {connected ? <PhoneOff size={22} /> : <Phone size={22} />}
            <span className="call-btn-label">
              {connected ? 'End Session' : 'Talk to Amani'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
