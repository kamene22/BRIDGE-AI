"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import Sidebar from "../components/Sidebar";
import ScamAlertBanner from "../components/ScamAlertBanner";
import CitationsAccordion from "../components/CitationsAccordion";
import { JOURNEYS } from "../components/UserJourneys";
import { sendChatMessage, getWelcomeMessage, ChatResponse } from "@/lib/api";
import { Send, PanelLeftOpen, Mic, Sparkles, RefreshCw, ChevronDown, Check } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  guardrails?: {
    scam_detected: boolean;
    legal_boundary_triggered: boolean;
    out_of_scope: boolean;
  };
  latency_ms?: number;
  intent?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMsg, setInputMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessionId] = useState(`session_${Date.now()}`);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Check if a pending prompt was passed from the landing page
  useEffect(() => {
    if (typeof window !== "undefined") {
      const pendingPrompt = sessionStorage.getItem("pending_prompt");
      if (pendingPrompt) {
        sessionStorage.removeItem("pending_prompt");
        handleSendQuery(pendingPrompt);
      }
    }
  }, []);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSendQuery = async (queryText?: string) => {
    const textToSend = queryText || inputMsg;
    if (!textToSend || !textToSend.trim() || isLoading) return;

    const userMessageId = `usr_${Date.now()}`;
    const newMessages: Message[] = [
      ...messages,
      { id: userMessageId, role: "user", content: textToSend }
    ];

    setMessages(newMessages);
    setInputMsg("");
    setIsLoading(true);

    try {
      const res: ChatResponse = await sendChatMessage(textToSend, sessionId);
      setMessages([
        ...newMessages,
        {
          id: `ast_${Date.now()}`,
          role: "assistant",
          content: res.answer,
          sources: res.sources,
          guardrails: res.guardrails,
          latency_ms: res.latency_ms,
          intent: res.intent
        }
      ]);
    } catch (error) {
      setMessages([
        ...newMessages,
        {
          id: `err_${Date.now()}`,
          role: "assistant",
          content: "I'm having trouble reaching the career mentor backend server right now. Please ensure the FastAPI server is running on http://127.0.0.1:8000."
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  return (
    <div className="flex h-screen bg-cream-100 text-charcoal-900 overflow-hidden font-sans">
      {/* Sidebar Component */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-cream-100">
        {/* Top Workspace Header */}
        <header className="h-16 border-b border-sand-300 px-6 flex items-center justify-between bg-cream-100/80 backdrop-blur-md shrink-0 z-10">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-xl text-muted-brown hover:text-charcoal-900 hover:bg-sand-200 transition-colors"
                title="Expand sidebar"
              >
                <PanelLeftOpen className="w-5 h-5" />
              </button>
            )}
            <div className="flex items-center gap-1.5 font-semibold text-charcoal-900">
              <span className="font-sans text-base">Bridge AI</span>
              <span className="w-2 h-2 rounded-full bg-terracotta-600"></span>
              <ChevronDown className="w-4 h-4 text-muted-brown" />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button className="px-4 py-1.5 rounded-full border border-sand-300 text-xs font-semibold text-charcoal-900 hover:bg-sand-200 transition-colors">
              Log in
            </button>
            <button className="px-4 py-1.5 rounded-full bg-charcoal-900 text-cream-100 text-xs font-semibold hover:bg-charcoal-800 transition-colors shadow-sm">
              Sign up for free
            </button>
          </div>
        </header>

        {/* Chat Content Body */}
        <main className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-3xl mx-auto min-h-full flex flex-col">
            {messages.length === 0 ? (
              /* Empty State Matching Image 4 */
              <div className="my-auto flex flex-col items-center justify-center text-center py-12">
                <div className="w-12 h-12 rounded-full bg-sand-200 flex items-center justify-center text-terracotta-600 mb-6 shadow-sm">
                  <Sparkles className="w-6 h-6" />
                </div>
                <h2 className="text-3xl font-serif font-semibold text-charcoal-900 tracking-tight mb-3">
                  Say what's on your mind.
                </h2>
                <p className="text-sm text-muted-brown max-w-md mb-8">
                  Ask about starting your first job, probation rules, interview prep, or spotting recruitment scams in Kenya.
                </p>

                {/* Quick Journey Cards Container */}
                <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-3 max-w-xl">
                  {JOURNEYS.slice(0, 4).map((j) => (
                    <button
                      key={j.id}
                      onClick={() => handleSendQuery(j.prompt)}
                      className="p-3.5 rounded-2xl bg-sand-200 hover:bg-sand-300/80 border border-sand-300/80 text-left transition-all hover:-translate-y-0.5 text-xs font-medium text-charcoal-900 flex items-center justify-between group"
                    >
                      <span className="line-clamp-1">{j.title}</span>
                      <span className="text-terracotta-600 font-bold group-hover:translate-x-0.5 transition-transform">→</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Chat Message Stream */
              <div className="space-y-6 pb-6">
                {messages.map((msg) => (
                  <div key={msg.id} className="w-full">
                    {msg.role === "user" ? (
                      /* User Message Bubble */
                      <div className="flex justify-end">
                        <div className="max-w-[80%] p-4 rounded-2xl rounded-tr-sm bg-charcoal-900 text-cream-100 text-sm font-sans shadow-sm leading-relaxed">
                          {msg.content}
                        </div>
                      </div>
                    ) : (
                      /* Assistant Mentor Bubble matching warm Amani style */
                      <div className="flex justify-start">
                        <div className="max-w-[88%] p-5 rounded-2xl rounded-tl-sm bg-sand-200 border border-sand-300 text-charcoal-900 shadow-sm leading-relaxed relative">
                          {/* Header Metadata */}
                          <div className="flex items-center justify-between text-xs text-muted-brown mb-3 pb-2 border-b border-sand-300/60">
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-terracotta-600"></span>
                              <span className="font-semibold text-charcoal-900 font-serif text-sm">Bridge AI Mentor</span>
                              {msg.intent && (
                                <span className="text-[10px] bg-cream-100 text-charcoal-900 px-2 py-0.5 rounded-full border border-sand-300 font-mono">
                                  {msg.intent}
                                </span>
                              )}
                            </div>
                            {msg.latency_ms && (
                              <span className="text-[10px] text-muted-brown font-mono">
                                ⚡ {msg.latency_ms}ms
                              </span>
                            )}
                          </div>

                          {/* Scam Banner if triggered */}
                          {msg.guardrails?.scam_detected && <ScamAlertBanner />}

                          {/* Response Text */}
                          <div className="text-sm font-sans whitespace-pre-line leading-relaxed text-charcoal-900">
                            {msg.content}
                          </div>

                          {/* Vector Sources Accordion */}
                          {msg.sources && <CitationsAccordion sources={msg.sources} />}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="p-4 rounded-2xl bg-sand-200 border border-sand-300 text-xs font-medium text-muted-brown flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 text-terracotta-600 animate-spin" />
                      <span>Bridge AI mentor is analyzing context & checking safety guardrails...</span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            )}
          </div>
        </main>

        {/* Bottom Floating Input Bar matching Image 4 */}
        <footer className="p-6 bg-cream-100/90 border-t border-sand-300 shrink-0">
          <div className="max-w-3xl mx-auto">
            <div className="relative flex items-center p-2 rounded-full bg-sand-200 border border-sand-300 shadow-md focus-within:border-charcoal-900 transition-colors">
              <span className="pl-4 pr-2 text-muted-brown font-semibold text-lg">+</span>
              <input
                type="text"
                value={inputMsg}
                onChange={(e) => setInputMsg(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendQuery()}
                placeholder="Ask anything..."
                className="w-full bg-transparent text-charcoal-900 placeholder:text-muted-brown/70 outline-none text-sm font-sans"
              />

              <div className="flex items-center gap-2 pr-1">
                <button
                  type="button"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-sand-300 text-charcoal-900 text-xs font-semibold hover:bg-sand-400/70 transition-colors"
                >
                  <Mic className="w-3.5 h-3.5 text-terracotta-600" />
                  <span>Voice</span>
                </button>

                <button
                  onClick={() => handleSendQuery()}
                  disabled={!inputMsg.trim() || isLoading}
                  className="w-9 h-9 rounded-full bg-charcoal-900 text-cream-100 flex items-center justify-center hover:bg-charcoal-800 disabled:opacity-40 transition-all shadow-sm"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
            <p className="text-center text-[11px] text-muted-brown mt-2">
              Bridge AI provides grounded guidance under the Kenya Employment Act. Verify sensitive legal decisions.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}
