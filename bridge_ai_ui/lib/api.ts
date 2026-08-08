const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

export interface ChatResponse {
  answer: string;
  sources: string[];
  redirected: boolean;
  guardrails: {
    scam_detected: boolean;
    legal_boundary_triggered: boolean;
    out_of_scope: boolean;
  };
  latency_ms: number;
  intent: string;
}

export async function sendChatMessage(message: string, sessionId: string = "default"): Promise<ChatResponse> {
  const response = await fetch(`${BACKEND_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getWelcomeMessage(): Promise<string> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/welcome`);
    if (response.ok) {
      const data = await response.json();
      return data.message;
    }
  } catch (_e) {
    console.warn("Backend welcome endpoint offline, fallback active.");
  }
  return "Hujambo! I'm Bridge AI (Amani), your career mentor. How can I support your journey today?";
}

export async function getTelemetry() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/telemetry`);
    if (response.ok) {
      return response.json();
    }
  } catch (_e) {
    console.warn("Backend telemetry offline.");
  }
  return null;
}

export async function resetSession(sessionId: string = "default") {
  try {
    await fetch(`${BACKEND_URL}/api/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
  } catch (_e) {
    console.warn("Reset failed.");
  }
}
