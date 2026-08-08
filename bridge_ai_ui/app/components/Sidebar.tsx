"use client";

import Link from "next/link";
import { Plus, Search, Mic, PanelLeftClose, User } from "lucide-react";

interface SidebarProps {
  onNewChat: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

export default function Sidebar({ onNewChat, isOpen, onToggle }: SidebarProps) {
  if (!isOpen) return null;

  return (
    <aside className="w-64 h-screen bg-cream-200 border-r border-sand-300 flex flex-col justify-between p-4 shrink-0 transition-all">
      <div>
        {/* Top Header & Collapse */}
        <div className="flex items-center justify-between mb-6 px-2">
          <Link href="/" className="flex items-center gap-1.5 font-semibold text-lg text-charcoal-900 font-sans">
            <span>Bridge AI</span>
            <span className="w-2 h-2 rounded-full bg-terracotta-600"></span>
          </Link>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg text-muted-brown hover:text-charcoal-900 hover:bg-sand-300/60 transition-colors"
            title="Collapse sidebar"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2 mb-6">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl bg-sand-100 hover:bg-sand-300 text-charcoal-900 text-sm font-medium border border-sand-300 shadow-sm transition-all text-left"
          >
            <Plus className="w-4 h-4 text-terracotta-600" />
            <span>New chat</span>
          </button>

          <button className="w-full flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-muted-brown hover:text-charcoal-900 hover:bg-sand-300/50 text-sm font-medium transition-colors text-left">
            <Search className="w-4 h-4" />
            <span>Search chats</span>
          </button>

          <button className="w-full flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-muted-brown hover:text-charcoal-900 hover:bg-sand-300/50 text-sm font-medium transition-colors text-left">
            <Mic className="w-4 h-4 text-terracotta-600" />
            <span>Voice mode (Beyond PoC)</span>
          </button>
        </div>

        {/* Recents Section */}
        <div className="px-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-muted-brown">
            RECENTS
          </span>
          <p className="text-xs text-muted-brown/80 mt-3 italic">
            No conversations yet.
          </p>
        </div>
      </div>

      {/* Bottom Profile Sync Card */}
      <div className="p-3.5 rounded-2xl bg-sand-100 border border-sand-300 space-y-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-charcoal-900">
          <User className="w-4 h-4 text-terracotta-600" />
          <span>Sync your progress</span>
        </div>
        <p className="text-[11px] text-muted-brown leading-tight">
          Sign in to save your session history across devices.
        </p>
        <button className="w-full mt-1 py-2 rounded-xl bg-charcoal-900 text-cream-100 text-xs font-medium hover:bg-charcoal-800 transition-colors">
          Sign in
        </button>
      </div>
    </aside>
  );
}
