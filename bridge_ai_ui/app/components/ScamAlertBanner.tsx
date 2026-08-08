"use client";

import { AlertTriangle, ShieldAlert } from "lucide-react";

export default function ScamAlertBanner() {
  return (
    <div className="w-full mb-4 p-4 rounded-2xl bg-red-950/10 border border-red-400/40 text-red-900 flex items-start gap-3 shadow-sm">
      <div className="p-2 rounded-xl bg-red-100 text-red-600 shrink-0">
        <ShieldAlert className="w-5 h-5" />
      </div>
      <div>
        <h5 className="font-semibold text-red-950 text-sm flex items-center gap-1.5">
          <span>⚠️ SCAM RED FLAG WARNING DETECTED</span>
        </h5>
        <p className="text-xs text-red-800/90 mt-1 leading-relaxed">
          Do not pay any upfront registration, medical check, or interview fees via M-Pesa or wire transfers! Legitimate employers and recruitment agencies in Kenya do not charge applicants fees.
        </p>
      </div>
    </div>
  );
}
