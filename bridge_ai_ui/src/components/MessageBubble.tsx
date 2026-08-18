import type { Message } from '../store/appStore';
import { AlertTriangle, Scale, ExternalLink } from 'lucide-react';
import './MessageBubble.css';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { role, text, guardrails, sources, isStreaming } = message;

  const time = new Date(message.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`message-bubble message-${role}`}>
      {/* Role badge */}
      <div className="message-header">
        <span className="message-role">
          {role === 'user' ? 'You' : role === 'amani' ? 'Amani' : 'System'}
        </span>
        <span className="message-time">{time}</span>
      </div>

      {/* Message text */}
      <div className="message-text">
        {text}
        {isStreaming && <span className="streaming-cursor" />}
      </div>

      {/* Guardrail badges */}
      {guardrails && (
        <div className="message-badges">
          {guardrails.legal_boundary_triggered && (
            <span className="badge badge-legal">
              <Scale size={12} />
              General guidance — not legal advice
            </span>
          )}
          {guardrails.scam_detected && (
            <span className="badge badge-scam">
              <AlertTriangle size={12} />
              Potential scam warning
            </span>
          )}
          {guardrails.out_of_scope && (
            <span className="badge badge-oos">
              Outside Bridge AI scope
            </span>
          )}
        </div>
      )}

      {/* Sources */}
      {sources && sources.length > 0 && (
        <details className="message-sources">
          <summary className="sources-summary">
            <ExternalLink size={12} />
            {sources.length} source{sources.length !== 1 ? 's' : ''}
          </summary>
          <ul className="sources-list">
            {sources.map((src, i) => (
              <li key={i} className="source-item">{src}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
