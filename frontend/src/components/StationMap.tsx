"use client";

import React from "react";
import { Navigation } from "lucide-react";

export default function StationMap({ telemetry }: { telemetry: any }) {
  const isRed = telemetry.densityStatus === "RED";
  const isYellow = telemetry.densityStatus === "YELLOW";
  const svgZoneFill = isRed ? "#ef4444" : isYellow ? "#f59e0b" : "#10b981";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Navigation className="w-4 h-4 text-emerald-400" />
          Live Digital Twin — Charbagh Station Blueprint
        </h3>
        <span className="text-xs text-slate-400">Dynamic SVG Node</span>
      </div>

      <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
        <svg viewBox="0 0 400 220" className="w-full h-auto">
          <rect x="20" y="20" width="360" height="40" rx="6" fill="#1e293b" stroke="#475569" strokeWidth="2" />
          <text x="35" y="45" fill="#cbd5e1" fontSize="12" fontWeight="bold">
            PLATFORM 1 (Festive Express Arrival)
          </text>

          <rect
            x="60"
            y="65"
            width="95"
            height="90"
            rx="6"
            fill={svgZoneFill}
            fillOpacity="0.25"
            stroke={svgZoneFill}
            strokeWidth="3"
          />
          <text x="78" y="105" fill="#ffffff" fontSize="12" fontWeight="bold">
            FOB - 1
          </text>
          <text x="72" y="125" fill="#e2e8f0" fontSize="10">
            Count: {telemetry.personCount}/{telemetry.maxCapacity}
          </text>

          <rect
            x="245"
            y="65"
            width="95"
            height="90"
            rx="6"
            fill="#10b981"
            fillOpacity={isRed ? "0.35" : "0.1"}
            stroke="#10b981"
            strokeWidth={isRed ? "3" : "1.5"}
          />
          <text x="265" y="105" fill="#ffffff" fontSize="12" fontWeight="bold">
            FOB - 2
          </text>
          <text x="255" y="125" fill="#a7f3d0" fontSize="10">
            {isRed ? "DIVERT HERE" : "Clear (12/45)"}
          </text>

          {isRed && (
            <g>
              <path d="M 165 110 L 235 110" stroke="#38bdf8" strokeWidth="3" strokeDasharray="6,4" />
              <polygon points="235,105 243,110 235,115" fill="#38bdf8" />
              <text x="168" y="98" fill="#38bdf8" fontSize="9" fontWeight="bold">
                PA REROUTE
              </text>
            </g>
          )}

          <rect x="20" y="160" width="360" height="40" rx="6" fill="#1e293b" stroke="#475569" strokeWidth="2" />
          <text x="115" y="185" fill="#cbd5e1" fontSize="12" fontWeight="bold">
            MAIN EXIT CONCOURSE & RPF POST
          </text>
        </svg>
      </div>
    </div>
  );
}