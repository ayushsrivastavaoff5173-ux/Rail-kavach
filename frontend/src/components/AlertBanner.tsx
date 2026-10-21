"use client";

import React from "react";
import { ShieldAlert } from "lucide-react";

interface AlertBannerProps {
  isRed: boolean;
  evacuationRoute: string;
}

export default function AlertBanner({ isRed, evacuationRoute }: AlertBannerProps) {
  if (!isRed) return null;

  return (
    <div className="mb-6 p-4 rounded-xl bg-red-950/80 border-2 border-red-500 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 animate-pulse">
      <div className="flex items-center gap-3">
        <ShieldAlert className="w-8 h-8 text-red-400 shrink-0" />
        <div>
          <h2 className="text-base font-bold text-red-200 uppercase tracking-wider">
            STAMPEDE RISK DETECTED — ACTIVE CLOSED-LOOP INTERVENTION ENGAGED
          </h2>
          <p className="text-sm text-red-300">{evacuationRoute}</p>
        </div>
      </div>
      <span className="px-3 py-1 rounded bg-red-600 text-white text-xs font-bold uppercase tracking-widest shrink-0">
        RPF Control Room Notified
      </span>
    </div>
  );
}