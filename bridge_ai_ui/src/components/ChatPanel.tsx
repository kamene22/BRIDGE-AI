import { useRef, useEffect, useState, type KeyboardEvent } from 'react';
import { useAppStore } from '../store/appStore';
import { MessageBubble } from './MessageBubble';
import { Send } from 'lucide-react';
import './ChatPanel.css';

export function ChatPanel() {
  const messages = useAppStore((s) => s.messages);
  const sendTextMessage = useAppStore((s) => s.sendTextMessage);
  const [inputText, setInputText] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    const text = inputText.trim();
    if (!text) return;
    setInputText('');
    sendTextMessage(text);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <h2 className="chat-title">Conversation</h2>
        <span className="chat-count">{messages.length} messages</span>
      </div>

      {/* Messages */}
      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p className="chat-empty-title">Welcome to Bridge AI</p>
            <p className="chat-empty-subtitle">
              Ask about jobs, interviews, employment rights, or career advice in Kenya.
            </p>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
      </div>

      {/* Input Bar */}
      <div className="chat-input-bar">
        <input
          ref={inputRef}
          id="chat-input"
          type="text"
          className="chat-input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Amani anything…"
          autoComplete="off"
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!inputText.trim()}
          aria-label="Send message"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
