import { useRef, useEffect, useMemo } from 'react';
import { useAppStore, type OrbState } from '../store/appStore';
import './LuminousOrb.css';

interface LuminousOrbProps {
  size?: number;
}

export function LuminousOrb({ size = 220 }: LuminousOrbProps) {
  const orbRef = useRef<HTMLDivElement>(null);
  const orbState = useAppStore((s) => s.orbState);
  const micAmplitude = useAppStore((s) => s.micAmplitude);
  const speakerAmplitude = useAppStore((s) => s.speakerAmplitude);
  const connected = useAppStore((s) => s.connected);

  const rafRef = useRef<number>(0);
  const amplitudeRef = useRef(0);

  useEffect(() => {
    const update = () => {
      const target =
        orbState === 'listening'
          ? micAmplitude
          : orbState === 'speaking'
          ? speakerAmplitude
          : 0;

      // Smooth interpolation for calm motion
      amplitudeRef.current += (target - amplitudeRef.current) * 0.12;

      if (orbRef.current) {
        orbRef.current.style.setProperty(
          '--amplitude',
          amplitudeRef.current.toFixed(3)
        );
      }

      rafRef.current = requestAnimationFrame(update);
    };

    rafRef.current = requestAnimationFrame(update);
    return () => cancelAnimationFrame(rafRef.current);
  }, [orbState, micAmplitude, speakerAmplitude]);

  const stateLabel = useMemo(() => {
    if (!connected && orbState === 'idle') return 'Talk to Amani';
    const labels: Record<OrbState, string> = {
      idle: 'Tap to connect',
      listening: "I'm listening...",
      speaking: 'Amani',
      thinking: 'Give me a second...',
    };
    return labels[orbState];
  }, [orbState, connected]);

  return (
    <div className="orb-container" style={{ '--orb-size': `${size}px` } as React.CSSProperties}>
      {/* Outer ambient glow */}
      <div className="orb-glow" data-state={orbState} />

      {/* Reactive amplitude ring */}
      <div className="orb-amplitude-ring" data-state={orbState} ref={orbRef} />

      {/* Main sphere */}
      <div className="orb-sphere" data-state={orbState}>
        <div className="orb-inner-core" />
        <div className="orb-specular" />

        {/* Subtle thinking pulse */}
        {orbState === 'thinking' && (
          <div className="orb-thinking-pulse" />
        )}
      </div>

      {/* Human State Label */}
      <span className="orb-label" data-state={orbState}>
        {stateLabel}
      </span>
    </div>
  );
}
