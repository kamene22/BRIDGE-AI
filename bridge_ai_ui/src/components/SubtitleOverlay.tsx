import { useAppStore } from '../store/appStore';
import './SubtitleOverlay.css';

export function SubtitleOverlay() {
  const userSubtitle = useAppStore((s) => s.userSubtitle);
  const amaniSubtitle = useAppStore((s) => s.amaniSubtitle);
  const orbState = useAppStore((s) => s.orbState);

  const showUser = orbState === 'listening' && userSubtitle.trim();
  const showAmani = orbState === 'speaking' && amaniSubtitle.trim();

  if (!showUser && !showAmani) return null;

  return (
    <div className="subtitle-overlay">
      {showUser && (
        <div className="subtitle subtitle-user">
          <span className="subtitle-indicator" />
          <span className="subtitle-text">{userSubtitle}</span>
        </div>
      )}
      {showAmani && (
        <div className="subtitle subtitle-amani">
          <span className="subtitle-text">{amaniSubtitle}</span>
        </div>
      )}
    </div>
  );
}
