/**
 * AudioEngine — Mic capture (16kHz) + Speaker playback (24kHz)
 * 
 * Wraps Web Audio API AudioWorklets for:
 * - Capturing microphone audio at 16kHz, converting to base64 PCM chunks
 * - Playing back Gemini Live 24kHz PCM audio chunks
 * - Exposing real-time RMS amplitude for the LuminousOrb
 */

export class AudioEngine {
  // Capture (mic → Gemini)
  private captureCtx: AudioContext | null = null;
  private captureWorklet: AudioWorkletNode | null = null;
  private captureStream: MediaStream | null = null;
  private _micAmplitude = 0;

  // Playback (Gemini → speakers)
  private playbackCtx: AudioContext | null = null;
  private playbackWorklet: AudioWorkletNode | null = null;
  private gainNode: GainNode | null = null;
  private _speakerAmplitude = 0;
  private _isPlaying = false;

  // Callbacks
  private onAudioChunk: ((base64: string, amplitude: number) => void) | null = null;

  get micAmplitude(): number { return this._micAmplitude; }
  get speakerAmplitude(): number { return this._speakerAmplitude; }
  get isPlaying(): boolean { return this._isPlaying; }

  // ── Capture ─────────────────────────────────────────────

  async startCapture(
    onChunk: (base64: string, amplitude: number) => void
  ): Promise<void> {
    this.onAudioChunk = onChunk;

    // Request mic at 16kHz mono
    this.captureStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    this.captureCtx = new AudioContext({ sampleRate: 16000 });
    if (this.captureCtx.state === 'suspended') { await this.captureCtx.resume(); }

    // Load capture worklet
    await this.captureCtx.audioWorklet.addModule('/audio-processors/capture.worklet.js');

    const source = this.captureCtx.createMediaStreamSource(this.captureStream);
    this.captureWorklet = new AudioWorkletNode(this.captureCtx, 'audio-capture-processor');

    // Handle PCM chunks from worklet
    this.captureWorklet.port.onmessage = (event) => {
      if (event.data.type === 'audio' && event.data.data) {
        const float32Data: Float32Array = event.data.data;

        // Compute RMS amplitude
        let sum = 0;
        for (let i = 0; i < float32Data.length; i++) {
          sum += float32Data[i] * float32Data[i];
        }
        this._micAmplitude = Math.sqrt(sum / float32Data.length);

        // Convert Float32 → Int16 PCM → Base64
        const int16 = new Int16Array(float32Data.length);
        for (let i = 0; i < float32Data.length; i++) {
          const s = Math.max(-1, Math.min(1, float32Data[i]));
          int16[i] = s * 0x7fff;
        }

        const bytes = new Uint8Array(int16.buffer);
        const base64 = this.uint8ToBase64(bytes);

        this.onAudioChunk?.(base64, this._micAmplitude);
      }
    };

    source.connect(this.captureWorklet);
    // Don't connect to destination — we don't want to hear our own mic
  }

  stopCapture(): void {
    this.captureWorklet?.disconnect();
    this.captureWorklet = null;

    if (this.captureStream) {
      this.captureStream.getTracks().forEach(t => t.stop());
      this.captureStream = null;
    }

    if (this.captureCtx) {
      this.captureCtx.close();
      this.captureCtx = null;
    }

    this._micAmplitude = 0;
    this.onAudioChunk = null;
  }

  // ── Playback ────────────────────────────────────────────

  async initPlayback(): Promise<void> {
    if (this.playbackCtx) return;

    this.playbackCtx = new AudioContext({ sampleRate: 24000 });

    if (this.playbackCtx.state === 'suspended') {
      await this.playbackCtx.resume();
    }

    await this.playbackCtx.audioWorklet.addModule('/audio-processors/playback.worklet.js');

    this.playbackWorklet = new AudioWorkletNode(this.playbackCtx, 'pcm-processor');
    this.gainNode = this.playbackCtx.createGain();
    this.gainNode.gain.value = 0.8;

    this.playbackWorklet.connect(this.gainNode);
    this.gainNode.connect(this.playbackCtx.destination);
  }

  async playChunk(base64PCM: string): Promise<void> {
    if (!this.playbackCtx || !this.playbackWorklet) {
      await this.initPlayback();
    }

    if (this.playbackCtx?.state === 'suspended') {
      await this.playbackCtx.resume();
    }

    // Base64 → Uint8 → Int16 → Float32
    const binaryString = atob(base64PCM);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    const int16 = new Int16Array(bytes.buffer);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / 32768;
    }

    // Compute speaker amplitude
    let sum = 0;
    for (let i = 0; i < float32.length; i++) {
      sum += float32[i] * float32[i];
    }
    this._speakerAmplitude = Math.sqrt(sum / float32.length);
    this._isPlaying = true;

    // Send to playback worklet
    this.playbackWorklet!.port.postMessage(float32);
  }

  interrupt(): void {
    if (this.playbackWorklet) {
      this.playbackWorklet.port.postMessage('interrupt');
    }
    this._speakerAmplitude = 0;
    this._isPlaying = false;
  }

  setVolume(volume: number): void {
    if (this.gainNode) {
      this.gainNode.gain.value = Math.max(0, Math.min(1, volume));
    }
  }

  // ── Cleanup ─────────────────────────────────────────────

  destroy(): void {
    this.stopCapture();
    this.interrupt();

    if (this.playbackCtx) {
      this.playbackCtx.close();
      this.playbackCtx = null;
    }

    this.playbackWorklet = null;
    this.gainNode = null;
  }

  // ── Util ────────────────────────────────────────────────

  private uint8ToBase64(bytes: Uint8Array): string {
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }
}
