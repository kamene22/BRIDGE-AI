"use client";

import Link from "next/link";
import { ArrowRight, MessageSquare, ShieldCheck } from "lucide-react";

interface NavbarProps {
  showChatLink?: boolean;
}

export default function Navbar({ showChatLink = true }: NavbarProps) {
  return (
    <header className="w-full py-6 px-8 flex items-center justify-between z-20 relative">
      <Link href="/" className="flex items-center gap-2 group">
        <span className="text-2xl font-semibold tracking-tight text-charcoal-900 font-sans">
          Bridge AI
        </span>
        <span className="w-2.5 h-2.5 rounded-full bg-terracotta-600 inline-block animate-pulse"></span>
      </Link>

      <div className="flex items-center gap-4">
        {showChatLink && (
          <Link
            href="/chat"
            className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-charcoal-900 text-cream-100 text-sm font-medium hover:bg-charcoal-800 transition-all shadow-sm hover:shadow-md"
          >
            <MessageSquare className="w-4 h-4" />
            <span>Open Chat</span>
            <ArrowRight className="w-4 h-4 ml-0.5" />
          </Link>
        )}
        <button className="px-5 py-2.5 rounded-full bg-sand-200 text-charcoal-900 text-sm font-medium hover:bg-sand-300 transition-all border border-sand-300">
          Sign in →
        </button>
      </div>
    </header>
  );
}
