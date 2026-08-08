"use client";

import { useState } from "react";
import { BookOpen, ChevronDown, FileText } from "lucide-react";

interface CitationsAccordionProps {
  sources: string[];
}

export default function CitationsAccordion({ sources }: CitationsAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-sand-300/80">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-xs font-medium text-muted-brown hover:text-charcoal-900 transition-colors py-1"
      >
        <span className="flex items-center gap-1.5">
          <BookOpen className="w-3.5 h-3.5 text-terracotta-600" />
          <span>📌 Verified Knowledge Grounding Citations ({sources.length})</span>
        </span>
        <ChevronDown
          className={`w-3.5 h-3.5 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div className="mt-2 space-y-1.5 pl-2">
          {sources.map((src, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 text-[11px] text-charcoal-800 bg-sand-200/60 px-3 py-1.5 rounded-lg border border-sand-300/50"
            >
              <FileText className="w-3 h-3 text-terracotta-600 shrink-0" />
              <span className="font-mono text-[10.5px] truncate">{src}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
