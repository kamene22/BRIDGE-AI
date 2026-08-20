/**
 * GeminiLiveClient — WebSocket manager for Gemini Live API
 * 
 * Ported directly from geminilive.js (vanilla JS) into TypeScript.
 * Aligned with working gemini-live-api-examples implementation.
 */

// ── Types ─────────────────────────────────────────────

export interface SessionConfig {
  model?: string;
  voiceName?: string;
  languagePreference?: 'adaptive' | 'english' | 'kiswahili' | 'sheng';
  systemInstruction?: string;
  temperature?: number;
}

export interface FunctionCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
}

export interface FunctionResponse {
  id: string;
  name: string;
  response: { result?: string; error?: string };
}

type ResponseType =
  | 'SETUP_COMPLETE'
  | 'AUDIO'
  | 'TEXT'
  | 'TOOL_CALL'
  | 'INPUT_TRANSCRIPTION'
  | 'OUTPUT_TRANSCRIPTION'
  | 'TURN_COMPLETE'
  | 'INTERRUPTED';

interface ParsedResponse {
  type: ResponseType;
  data: unknown;
}

// ── Client ────────────────────────────────────────────

export class GeminiLiveClient {
  private ws: WebSocket | null = null;
  private token: string;
  private config: SessionConfig;
  private _connected = false;
  private intentionalClose = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  // Callbacks
  onSetupComplete: (() => void) | null = null;
  onAudioChunk: ((base64: string) => void) | null = null;
  onText: ((text: string) => void) | null = null;
  onToolCall: ((calls: FunctionCall[]) => void) | null = null;
  onInputTranscription: ((text: string, finished: boolean) => void) | null = null;
  onOutputTranscription: ((text: string, finished: boolean) => void) | null = null;
  onTurnComplete: (() => void) | null = null;
  onInterrupted: (() => void) | null = null;
  onClose: (() => void) | null = null;
  onError: ((error: string) => void) | null = null;

  get connected(): boolean { return this._connected; }

  constructor(token: string, config: SessionConfig = {}) {
    const langPref = config.languagePreference || 'adaptive';
    this.token = token;
    this.config = {
      model: config.model || 'gemini-3.1-flash-live-preview',
      voiceName: config.voiceName || 'Kore',
      temperature: config.temperature ?? 1.0,
      systemInstruction: config.systemInstruction || this.defaultSystemInstruction(langPref),
    };
  }

  private defaultSystemInstruction(langPref: string = 'adaptive'): string {
    let langDirective = "Follow the user's lead on language and register naturally (English, Kiswahili, or Sheng). Do not force slang or dialect unless the user uses it first.";
    if (langPref === 'english') {
      langDirective = "Communicate primarily in clear, warm, professional English.";
    } else if (langPref === 'kiswahili') {
      langDirective = "Communicate primarily in natural, warm Kiswahili.";
    } else if (langPref === 'sheng') {
      langDirective = "Communicate in natural Sheng.";
    }

    return `You are Amani, a calm, modern, intelligent, and warm career companion for young professionals navigating work.

IDENTITY AND TONE:
- You are a calm, supportive human companion. Sound natural, relaxed, and thoughtful — not like a corporate HR manual or a robotic voice agent demo.
- Never hardcode stereotypical tropes, forced slang, or assumptions about the user's age, graduate status, or employer.
- Language Instruction: ${langDirective}

FIRST MESSAGE REQUIREMENT:
When the session starts, say out loud: "Hey there, I'm Amani. Think of me as your sounding board for anything workplace or career-related." Keep it short, natural, and warm. Do not give unprompted career advice immediately.

CRITICAL RULES:
1. When users ask factual questions about employment law, probation, contracts, salary, or job scams, you MUST call search_knowledge_base to get grounded information before answering. Never guess legal facts.
2. When citing employment law, add: "This is general guidance, not legal advice. For your specific situation, consult a licensed advocate."
3. If you detect a potential job scam (upfront payment requests, unverified recruiters), explain the pattern calmly and recommend verification.
4. Keep responses concise and conversational — this is a voice conversation.`;
  }

  // ── Connection ──────────────────────────────────────

  connect(): void {
    const url = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContentConstrained?access_token=${this.token}`;
    
    console.log('[GeminiLive] Connecting to:', url);
    this.intentionalClose = false;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('[GeminiLive] WebSocket open');
      this._connected = true;
      this.reconnectAttempts = 0;
      this.sendSetupMessage();
    };

    this.ws.onclose = (event) => {
      console.log('[GeminiLive] WebSocket closed:', event.code, event.reason);
      this._connected = false;

      if (!this.intentionalClose && this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        console.log(`[GeminiLive] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), delay);
      } else {
        this.onClose?.();
      }
    };

    this.ws.onerror = (event) => {
      console.error('[GeminiLive] WebSocket error:', event);
      this._connected = false;
      this.onError?.('WebSocket connection error');
    };

    this.ws.onmessage = (event) => this.handleMessage(event);
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._connected = false;
  }

  // ── Send Methods ────────────────────────────────────

  sendAudio(base64PCM: string): void {
    this.send({
      realtimeInput: {
        audio: { mimeType: 'audio/pcm', data: base64PCM },
      },
    });
  }

  sendText(text: string): void {
    this.send({
      realtimeInput: { text },
    });
  }

  sendToolResponse(responses: FunctionResponse[]): void {
    console.log('[GeminiLive] Sending tool response:', responses);
    this.send({
      toolResponse: {
        functionResponses: responses,
      },
    });
  }

  updateToken(newToken: string): void {
    this.token = newToken;
  }

  // ── Private ─────────────────────────────────────────

  private send(message: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  private sendSetupMessage(): void {
    const setup = {
      setup: {
        model: `models/${this.config.model}`,
        generationConfig: {
          responseModalities: ['AUDIO'],
          temperature: this.config.temperature,
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: {
                voiceName: this.config.voiceName,
              },
            },
          },
        },
        systemInstruction: {
          parts: [{ text: this.config.systemInstruction }],
        },
        tools: [
          {
            functionDeclarations: [
              {
                name: 'search_knowledge_base',
                description:
                  "Search Bridge AI's knowledge base for grounded information about Kenyan employment law, career advice, job scams, interview preparation, probation rights, salary negotiations, and workplace guidance. Call this tool whenever the user asks factual questions about employment in Kenya.",
                parameters: {
                  type: 'OBJECT',
                  properties: {
                    query: {
                      type: 'STRING',
                      description: 'The search query to find relevant knowledge',
                    },
                  },
                  required: ['query'],
                },
              },
            ],
          },
        ],
        inputAudioTranscription: {},
        outputAudioTranscription: {},
        realtimeInputConfig: {
          automaticActivityDetection: {
            disabled: false,
            silenceDurationMs: 500,
            prefixPaddingMs: 200,
            endOfSpeechSensitivity: 'END_SENSITIVITY_HIGH',
            startOfSpeechSensitivity: 'START_SENSITIVITY_LOW',
          },
          activityHandling: 'ACTIVITY_HANDLING_UNSPECIFIED',
          turnCoverage: 'TURN_INCLUDES_ONLY_ACTIVITY',
        },
      },
    };

    console.log('[GeminiLive] Sending setup message:', setup);
    this.send(setup);
  }

  private async handleMessage(event: MessageEvent): Promise<void> {
    let jsonData: string;

    if (event.data instanceof Blob) {
      jsonData = await event.data.text();
    } else if (event.data instanceof ArrayBuffer) {
      jsonData = new TextDecoder().decode(event.data);
    } else {
      jsonData = event.data;
    }

    try {
      const data = JSON.parse(jsonData);
      const responses = this.parseResponses(data);

      for (const response of responses) {
        this.dispatchResponse(response);
      }
    } catch (err) {
      console.error('[GeminiLive] Parse error:', err);
    }
  }

  private parseResponses(data: Record<string, unknown>): ParsedResponse[] {
    const responses: ParsedResponse[] = [];
    const serverContent = data.serverContent as Record<string, unknown> | undefined;
    const modelTurn = serverContent?.modelTurn as Record<string, unknown> | undefined;
    const parts = modelTurn?.parts as Array<Record<string, unknown>> | undefined;

    // Setup complete
    if (data.setupComplete) {
      responses.push({ type: 'SETUP_COMPLETE', data: null });
      return responses;
    }

    // Tool call
    if (data.toolCall) {
      const tc = data.toolCall as Record<string, unknown>;
      responses.push({ type: 'TOOL_CALL', data: tc });
      return responses;
    }

    // Audio + text from model turn parts
    if (parts?.length) {
      for (const part of parts) {
        const inlineData = part.inlineData as Record<string, string> | undefined;
        if (inlineData) {
          responses.push({ type: 'AUDIO', data: inlineData.data });
        } else if (part.text) {
          responses.push({ type: 'TEXT', data: part.text });
        }
      }
    }

    // Input transcription
    if (serverContent?.inputTranscription) {
      const t = serverContent.inputTranscription as { text?: string; finished?: boolean };
      responses.push({
        type: 'INPUT_TRANSCRIPTION',
        data: { text: t.text || '', finished: t.finished || false },
      });
    }

    // Output transcription
    if (serverContent?.outputTranscription) {
      const t = serverContent.outputTranscription as { text?: string; finished?: boolean };
      responses.push({
        type: 'OUTPUT_TRANSCRIPTION',
        data: { text: t.text || '', finished: t.finished || false },
      });
    }

    // Turn complete
    if (serverContent?.turnComplete) {
      responses.push({ type: 'TURN_COMPLETE', data: null });
    }

    // Interrupted
    if (serverContent?.interrupted) {
      responses.push({ type: 'INTERRUPTED', data: null });
    }

    return responses;
  }

  private dispatchResponse(response: ParsedResponse): void {
    switch (response.type) {
      case 'SETUP_COMPLETE':
        console.log('[GeminiLive] Setup complete');
        this.onSetupComplete?.();
        break;

      case 'AUDIO':
        this.onAudioChunk?.(response.data as string);
        break;

      case 'TEXT':
        this.onText?.(response.data as string);
        break;

      case 'TOOL_CALL': {
        const tc = response.data as { functionCalls?: FunctionCall[] };
        if (tc.functionCalls?.length) {
          console.log('[GeminiLive] Tool call:', tc.functionCalls.map(f => f.name));
          this.onToolCall?.(tc.functionCalls);
        }
        break;
      }

      case 'INPUT_TRANSCRIPTION': {
        const t = response.data as { text: string; finished: boolean };
        this.onInputTranscription?.(t.text, t.finished);
        break;
      }

      case 'OUTPUT_TRANSCRIPTION': {
        const t = response.data as { text: string; finished: boolean };
        this.onOutputTranscription?.(t.text, t.finished);
        break;
      }

      case 'TURN_COMPLETE':
        console.log('[GeminiLive] Turn complete');
        this.onTurnComplete?.();
        break;

      case 'INTERRUPTED':
        console.log('[GeminiLive] Interrupted');
        this.onInterrupted?.();
        break;
    }
  }
}
