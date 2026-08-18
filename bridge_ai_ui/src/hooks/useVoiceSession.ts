/**
 * useVoiceSession — Hook that wires GeminiLiveClient + AudioEngine + Zustand store
 * 
 * This is the integration layer. It handles:
 * 1. Fetching ephemeral token from FastAPI
 * 2. Connecting to Gemini Live with the token
 * 3. Starting mic capture and routing audio to Gemini
 * 4. Playing back Gemini audio responses
 * 5. Relaying function calls to FastAPI for RAG
 * 6. Updating Zustand store with transcripts, amplitude, and orb state
 */

import { useRef, useCallback, useEffect } from 'react';
import { useAppStore } from '../store/appStore';
import { GeminiLiveClient } from '../services/geminiLiveClient';
import type { FunctionCall } from '../services/geminiLiveClient';
import { AudioEngine } from '../services/audioEngine';

export function useVoiceSession() {
  const clientRef = useRef<GeminiLiveClient | null>(null);
  const audioRef = useRef<AudioEngine | null>(null);
  const amplitudeRafRef = useRef<number>(0);
  const tokenExpiryRef = useRef<number>(0);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Store actions (stable references)
  const store = useAppStore;

  // ── Amplitude Loop ──────────────────────────────────

  const startAmplitudeLoop = useCallback(() => {
    const update = () => {
      const engine = audioRef.current;
      if (engine) {
        store.setState({
          micAmplitude: engine.micAmplitude,
          speakerAmplitude: engine.speakerAmplitude,
        });
      }
      amplitudeRafRef.current = requestAnimationFrame(update);
    };
    amplitudeRafRef.current = requestAnimationFrame(update);
  }, []);

  const stopAmplitudeLoop = useCallback(() => {
    cancelAnimationFrame(amplitudeRafRef.current);
    store.setState({ micAmplitude: 0, speakerAmplitude: 0 });
  }, []);

  // ── Function Call Relay ─────────────────────────────

  const handleToolCalls = useCallback(async (calls: FunctionCall[]) => {
    const client = clientRef.current;
    if (!client) return;

    store.setState({ orbState: 'thinking' });

    const responses = await Promise.all(
      calls.map(async (call) => {
        try {
          const res = await fetch('/api/voice-rag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              function_name: call.name,
              arguments: call.args,
              session_id: store.getState().sessionId,
            }),
          });

          if (!res.ok) {
            throw new Error(`FastAPI returned ${res.status}`);
          }

          const data = await res.json();

          // Store guardrail flags for UI badges
          const guardrails = data.guardrails || {};

          // Format the RAG chunks for Gemini Live to speak
          let resultText = data.answer || '';
          if (data.sources?.length) {
            resultText += `\n\nSources: ${data.sources.join(', ')}`;
          }
          if (guardrails.legal_boundary_triggered) {
            resultText += '\n\nReminder: This is general guidance, not legal advice.';
          }

          // Store latest guardrails for when the response commits
          store.setState({ _pendingGuardrails: guardrails, _pendingSources: data.sources } as Partial<ReturnType<typeof store.getState>>);

          return {
            id: call.id,
            name: call.name,
            response: { result: resultText },
          };
        } catch (err) {
          console.error('[VoiceSession] Tool call error:', err);
          return {
            id: call.id,
            name: call.name,
            response: { error: `Failed to search knowledge base: ${err}` },
          };
        }
      })
    );

    client.sendToolResponse(responses);
  }, []);

  // ── Token Management ────────────────────────────────

  const fetchToken = useCallback(async (): Promise<string> => {
    const res = await fetch('/api/token', { method: 'POST' });
    if (!res.ok) throw new Error(`Token fetch failed: ${res.status}`);
    const data = await res.json();
    tokenExpiryRef.current = new Date(data.expires_at).getTime();

    // Schedule refresh 2 minutes before expiry
    const refreshIn = tokenExpiryRef.current - Date.now() - 120_000;
    if (refreshIn > 0) {
      refreshTimerRef.current = setTimeout(async () => {
        try {
          const newToken = await fetchToken();
          clientRef.current?.updateToken(newToken);
          console.log('[VoiceSession] Token refreshed');
        } catch (e) {
          console.error('[VoiceSession] Token refresh failed:', e);
        }
      }, refreshIn);
    }

    return data.token;
  }, []);

  // ── Connect Voice Session ───────────────────────────

  const connectVoice = useCallback(async () => {
    try {
      store.getState().addMessage({ role: 'system', text: 'Connecting to voice session…' });

      // 1. Fetch ephemeral token
      const token = await fetchToken();

      // 2. Create audio engine
      audioRef.current = new AudioEngine();
      await audioRef.current.initPlayback();

      // 3. Create Gemini Live client
      // 3. Create Gemini Live client with voice and language preference
      const { voiceName, languagePreference } = store.getState();
      const client = new GeminiLiveClient(token, { voiceName, languagePreference });

      // 4. Wire callbacks
      client.onSetupComplete = () => {
        console.log('[VoiceSession] Setup complete');
        store.setState({ connected: true, orbState: 'speaking' });
        // Auto-trigger Amani's spoken introduction
        client.sendText('Please say out loud warmly and naturally: "Hey there, I\'m Amani. I\'m here if you want to talk something through." Do not add unprompted career advice.');

        // Auto-start microphone capture so Amani listens to user speech immediately
        audioRef.current?.startCapture((base64, _amplitude) => {
          clientRef.current?.sendAudio(base64);
        }).then(() => {
          store.setState({ voiceEnabled: true });
          startAmplitudeLoop();
        }).catch((err) => {
          console.error('[VoiceSession] Mic auto-start error:', err);
        });
      };

      client.onAudioChunk = (base64) => {
        audioRef.current?.playChunk(base64);
        if (store.getState().orbState !== 'speaking') {
          store.setState({ orbState: 'speaking' });
        }
      };

      client.onText = (text) => {
        store.getState().updateLastAmaniMessage(text);
      };

      client.onToolCall = handleToolCalls;

      client.onInputTranscription = (text, finished) => {
        if (finished) {
          store.getState().commitUserSubtitle();
        } else {
          store.setState({ userSubtitle: store.getState().userSubtitle + text });
        }
      };

      client.onOutputTranscription = (text, finished) => {
        if (finished) {
          // Commit the streaming message
          store.getState().commitAmaniMessage();
          store.setState({ amaniSubtitle: '' });
        } else {
          store.setState({ amaniSubtitle: store.getState().amaniSubtitle + text });
          store.getState().updateLastAmaniMessage(text);
        }
      };

      client.onTurnComplete = () => {
        store.getState().commitAmaniMessage();
        store.setState({ orbState: 'idle', amaniSubtitle: '' });
        audioRef.current?.interrupt(); // Ensure clean state
      };

      client.onInterrupted = () => {
        console.log('[VoiceSession] Interrupted — flushing audio');
        audioRef.current?.interrupt();
        store.getState().commitAmaniMessage();
        store.setState({ orbState: 'listening', amaniSubtitle: '' });
      };

      client.onClose = () => {
        store.setState({ connected: false, orbState: 'idle', voiceEnabled: false });
        store.getState().addMessage({ role: 'system', text: 'Voice session ended.' });
        stopAmplitudeLoop();
      };

      client.onError = (error) => {
        store.getState().addMessage({ role: 'system', text: `Voice error: ${error}` });
      };

      // 5. Connect
      clientRef.current = client;
      client.connect();
    } catch (err) {
      console.error('[VoiceSession] Connection error:', err);
      store.getState().addMessage({ role: 'system', text: `Failed to connect: ${err}` });
      store.setState({ connected: false, orbState: 'idle' });
    }
  }, [fetchToken, handleToolCalls, stopAmplitudeLoop]);

  // ── Toggle Mic ──────────────────────────────────────

  const toggleMic = useCallback(async () => {
    const { voiceEnabled } = store.getState();

    if (voiceEnabled) {
      // Stop mic
      audioRef.current?.stopCapture();
      store.setState({ voiceEnabled: false, orbState: 'idle', userSubtitle: '' });
      stopAmplitudeLoop();
    } else {
      // Start mic
      try {
        await audioRef.current?.startCapture((base64, _amplitude) => {
          clientRef.current?.sendAudio(base64);
        });
        store.setState({ voiceEnabled: true, orbState: 'listening' });
        startAmplitudeLoop();
      } catch (err) {
        console.error('[VoiceSession] Mic error:', err);
        store.getState().addMessage({ role: 'system', text: `Microphone error: ${err}` });
      }
    }
  }, [startAmplitudeLoop, stopAmplitudeLoop]);

  // ── Disconnect ──────────────────────────────────────

  const disconnectVoice = useCallback(() => {
    clientRef.current?.disconnect();
    clientRef.current = null;
    audioRef.current?.destroy();
    audioRef.current = null;
    stopAmplitudeLoop();
    clearTimeout(refreshTimerRef.current);

    store.setState({
      connected: false,
      orbState: 'idle',
      voiceEnabled: false,
      userSubtitle: '',
      amaniSubtitle: '',
    });
  }, [stopAmplitudeLoop]);

  // ── Send Prompt Chip ────────────────────────────────
  const sendPrompt = useCallback(async (promptText: string) => {
    const client = clientRef.current;
    const connected = store.getState().connected;

    if (connected && client) {
      store.getState().addMessage({ role: 'user', text: promptText });
      store.setState({ orbState: 'thinking' });
      client.sendText(promptText);
    } else {
      await store.getState().sendTextMessage(promptText);
    }
  }, []);

  // ── Cleanup on unmount ──────────────────────────────

  useEffect(() => {
    return () => {
      clientRef.current?.disconnect();
      audioRef.current?.destroy();
      cancelAnimationFrame(amplitudeRafRef.current);
      clearTimeout(refreshTimerRef.current);
    };
  }, []);

  return { connectVoice, disconnectVoice, toggleMic, sendPrompt };
}
