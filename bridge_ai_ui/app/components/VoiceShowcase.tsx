"use client";

import { useState } from "react";
import { Mic, PhoneOff, Keyboard, Sparkles } from "lucide-react";

export default function VoiceShowcase() {
  const [activeTab, setActiveTab] = useState<"voice" | "chat">("voice");

  return (
    <div className="w-full max-w-5xl mx-auto my-16 p-8 rounded-3xl bg-sand-200/80 border border-sand-300 shadow-sm relative overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* Left Side: Mockup Call Container */}
        <div className="flex flex-col items-center">
          {/* Dual Toggle Pill */}
          <div className="inline-flex p-1.5 rounded-full bg-sand-300 border border-sand-400 mb-6">
            <button
              onClick={() => setActiveTab("voice")}
              className={`px-5 py-2 rounded-full text-xs font-semibold transition-all ${
                activeTab === "voice"
                  ? "bg-charcoal-900 text-cream-100 shadow-sm"
                  : "text-muted-brown hover:text-charcoal-900"
              }`}
            >
              Voice
            </button>
            <button
              onClick={() => setActiveTab("chat")}
              className={`px-5 py-2 rounded-full text-xs font-semibold transition-all ${
                activeTab === "chat"
                  ? "bg-charcoal-900 text-cream-100 shadow-sm"
                  : "text-muted-brown hover:text-charcoal-900"
              }`}
            >
              Chat
            </button>
          </div>

          {/* Call Screen Card */}
          <div className="w-full max-w-md rounded-2xl bg-cream-100 border border-sand-300 p-6 shadow-md relative overflow-hidden">
            {/* Header Status */}
            <div className="flex items-center justify-between text-xs text-muted-brown mb-6">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-terracotta-600 animate-ping"></span>
                <span className="font-semibold text-charcoal-900">Bridge AI</span>
                <span className="text-[10px] text-muted-brown">• live on call</span>
              </div>
              <span className="font-mono text-[11px]">01:04</span>
            </div>

            {/* Overlapping Circles Abstract Artwork */}
            <div className="relative w-full h-36 flex items-center justify-center my-4">
              <div className="w-24 h-24 rounded-full bg-charcoal-900 shadow-lg absolute -translate-x-6"></div>
              <div className="w-24 h-24 rounded-full bg-terracotta-500 opacity-85 shadow-lg absolute translate-x-6"></div>
            </div>

            {/* Audio Waveform Bars */}
            <div className="flex items-center justify-center gap-1 my-6 h-8">
              {[40, 70, 30, 90, 60, 100, 45, 80, 50, 95, 60, 30, 85, 40].map((height, i) => (
                <div
                  key={i}
                  className="w-1.5 rounded-full bg-terracotta-600 transition-all duration-300 animate-pulse"
                  style={{ height: `${height}%`, animationDelay: `${i * 80}ms` }}
                ></div>
              ))}
            </div>

            {/* User Transcript Quote */}
            <p className="text-center text-xs text-muted-brown italic mb-6">
              You: <span className="text-charcoal-900 font-medium font-serif text-sm">"I just landed my first job after university!"</span>
            </p>

            {/* Controls Row */}
            <div className="flex items-center justify-center gap-4">
              <button className="w-10 h-10 rounded-full bg-sand-200 text-charcoal-900 flex items-center justify-center hover:bg-sand-300 transition-colors">
                <Mic className="w-4 h-4" />
              </button>
              <button className="w-12 h-12 rounded-full bg-red-600 text-white flex items-center justify-center hover:bg-red-700 shadow-md transition-all">
                <PhoneOff className="w-5 h-5" />
              </button>
              <button className="w-10 h-10 rounded-full bg-sand-200 text-charcoal-900 flex items-center justify-center hover:bg-sand-300 transition-colors">
                <Keyboard className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Feature Narrative */}
        <div className="space-y-8">
          <div>
            <div className="flex items-center gap-2 text-terracotta-600 text-xs font-bold uppercase tracking-wider mb-2">
              <Sparkles className="w-4 h-4" />
              <span>Grounded Mentorship</span>
            </div>
            <h3 className="text-3xl font-serif font-semibold text-charcoal-900 tracking-tight leading-tight">
              Say what's on your mind
            </h3>
            <p className="text-sm text-muted-brown mt-2 leading-relaxed">
              Open Bridge AI and just start asking — about probation rules, interview prep, salary taxes, or verifying suspicious job offers. No setup needed.
            </p>
          </div>

          <div className="pt-4 border-t border-sand-300">
            <h4 className="text-lg font-serif font-semibold text-charcoal-900">
              Bridge AI listens, then reflects
            </h4>
            <p className="text-sm text-muted-brown mt-1 leading-relaxed">
              Grounds advice in the Kenya Employment Act and 7 verified workplace corpuses before answering back.
            </p>
          </div>

          <div className="pt-4 border-t border-sand-300">
            <h4 className="text-lg font-serif font-semibold text-charcoal-900">
              Switch voice ↔ chat anytime
            </h4>
            <p className="text-sm text-muted-brown mt-1 leading-relaxed">
              Same thread, same memory. Continue your career conversation wherever you are.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
