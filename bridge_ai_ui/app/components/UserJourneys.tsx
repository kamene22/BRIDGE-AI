"use client";

import { Briefcase, Scale, AlertTriangle, UserCheck, DollarSign, ArrowUpRight } from "lucide-react";

export interface Journey {
  id: string;
  icon: any;
  category: string;
  title: string;
  prompt: string;
  badge: string;
}

export const JOURNEYS: Journey[] = [
  {
    id: "first_job",
    icon: Briefcase,
    category: "Career Launch",
    title: "Landed My First Job",
    prompt: "I just landed my first professional job after university! How do I prepare for my first week and set myself up for long-term success?",
    badge: "First Job Prep"
  },
  {
    id: "probation",
    icon: Scale,
    category: "Employment Rights",
    title: "Probation Extension",
    prompt: "I'm 4 months into my probation in Kenya and my manager wants to extend it. What are my legal rights under the Kenya Employment Act?",
    badge: "Probation Rights"
  },
  {
    id: "scam",
    icon: AlertTriangle,
    category: "Safety Guardrail",
    title: "M-Pesa Job Fee Check",
    prompt: "A recruiter asked for a KES 2,500 registration fee via M-Pesa before my job interview. Is this legitimate or a scam?",
    badge: "Scam Verification"
  },
  {
    id: "etiquette",
    icon: UserCheck,
    category: "Hidden Curriculum",
    title: "First Day Presentation",
    prompt: "How do I dress, present myself, and communicate with senior leadership on my first day at a white-collar office in Nairobi?",
    badge: "Workplace Etiquette"
  },
  {
    id: "salary",
    icon: DollarSign,
    category: "Financial Literacy",
    title: "First Salary Deductions",
    prompt: "How do I calculate statutory PAYE, NSSF, and SHIF deductions from my first salary offer in Kenya?",
    badge: "Salary & Tax Literacy"
  }
];

interface UserJourneysProps {
  onSelectJourney: (prompt: string) => void;
}

export default function UserJourneys({ onSelectJourney }: UserJourneysProps) {
  return (
    <div className="w-full max-w-4xl mx-auto my-8">
      <div className="text-center mb-6">
        <span className="text-xs font-semibold uppercase tracking-widest text-muted-brown bg-sand-200 px-4 py-1.5 rounded-full border border-sand-300">
          • EXPLORE USER JOURNEYS
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {JOURNEYS.map((journey) => {
          const Icon = journey.icon;
          return (
            <button
              key={journey.id}
              onClick={() => onSelectJourney(journey.prompt)}
              className="group text-left p-5 rounded-2xl bg-sand-200 hover:bg-sand-300/80 border border-sand-300/70 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg flex flex-col justify-between relative overflow-hidden"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-cream-100 flex items-center justify-center text-charcoal-900 shadow-sm group-hover:scale-105 transition-transform">
                    <Icon className="w-5 h-5 text-terracotta-600" />
                  </div>
                  <span className="text-[11px] font-medium text-muted-brown bg-cream-100 px-2.5 py-1 rounded-full border border-sand-300">
                    {journey.badge}
                  </span>
                </div>
                <h4 className="font-semibold text-charcoal-900 text-base mb-1 group-hover:text-terracotta-600 transition-colors">
                  {journey.title}
                </h4>
                <p className="text-xs text-muted-brown line-clamp-2 leading-relaxed">
                  "{journey.prompt}"
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-sand-300/60 flex items-center justify-between text-xs font-medium text-charcoal-900">
                <span>Start journey</span>
                <ArrowUpRight className="w-4 h-4 text-terracotta-600 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
