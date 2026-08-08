"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "./components/Navbar";
import UserJourneys from "./components/UserJourneys";
import VoiceShowcase from "./components/VoiceShowcase";
import { ArrowRight, Sparkles } from "lucide-react";

export default function LandingPage() {
  const router = useRouter();
  const [promptText, setPromptText] = useState("");

  const handleLaunchChat = (customPrompt?: string) => {
    const textToSend = customPrompt || promptText || "How do I prepare for my first job?";
    // Store selected prompt in sessionStorage to pass to /chat page
    if (typeof window !== "undefined") {
      sessionStorage.setItem("pending_prompt", textToSend);
    }
    router.push("/chat");
  };

  return (
    <div className="min-h-screen bg-cream-100 text-charcoal-900 flex flex-col relative selection:bg-terracotta-500 selection:text-white">
      {/* Ambient Radial Glow */}
      <div className="ambient-glow top-0 left-1/2 -translate-x-1/2 opacity-70"></div>

      {/* Header Navigation */}
      <Navbar />

      {/* Hero Section */}
      <main className="flex-1 w-full max-w-5xl mx-auto px-6 pt-12 pb-20 z-10 flex flex-col items-center text-center">
        {/* Capsule Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sand-200 border border-sand-300 mb-8 shadow-sm">
          <span className="w-2 h-2 rounded-full bg-terracotta-600"></span>
          <span className="text-xs font-semibold uppercase tracking-widest text-muted-brown">
            A CALM PLACE TO THINK OUT LOUD
          </span>
        </div>

        {/* Hero Headline */}
        <h1 className="text-5xl md:text-7xl font-serif font-bold text-charcoal-900 tracking-tight leading-[1.08] max-w-3xl mb-6">
          Say what you're still figuring out.
        </h1>

        {/* Subtitle */}
        <p className="text-lg md:text-xl text-muted-brown max-w-xl mb-12 font-sans font-light leading-relaxed">
          A grounded place to think out loud — about your <strong className="font-normal text-charcoal-900">first job</strong>, career decisions, probation rights, or spotting scams. Without judgement.
        </p>

        {/* Floating Input Card (Image 2 style) */}
        <div className="w-full max-w-2xl p-6 rounded-3xl bg-sand-200/90 border border-sand-300 shadow-lg backdrop-blur-md transition-all hover:shadow-xl mb-12">
          <textarea
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder="I just landed my first job after university and don't know where to start..."
            rows={3}
            className="w-full bg-transparent text-charcoal-900 placeholder:text-muted-brown/70 resize-none outline-none text-base font-sans leading-relaxed"
          />

          <div className="flex items-center justify-between mt-4 pt-3 border-t border-sand-300/80">
            <span className="text-xs text-muted-brown font-medium">
              Press enter · confidential mentor session
            </span>

            <button
              onClick={() => handleLaunchChat()}
              className="flex items-center gap-2 px-6 py-3 rounded-full bg-charcoal-900 text-cream-100 font-medium text-sm hover:bg-charcoal-800 transition-all shadow-md hover:shadow-lg active:scale-95"
            >
              <span>Talk now</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* User Journeys Floating Containers */}
        <UserJourneys onSelectJourney={(prompt) => handleLaunchChat(prompt)} />

        {/* Feature Showcase Section (Image 3 style) */}
        <VoiceShowcase />
      </main>

      {/* Footer */}
      <footer className="w-full py-8 border-t border-sand-300 text-center text-xs text-muted-brown z-10">
        <p>Bridge AI (Amani) — Grounded Kenya Career Mentorship Engine</p>
      </footer>
    </div>
  );
}
