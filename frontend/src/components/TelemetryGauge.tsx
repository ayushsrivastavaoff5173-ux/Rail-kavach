"use client";

import React from "react";
import { Users, Activity, Navigation } from "lucide-react";

export default function TelemetryGauge({ telemetry }: { telemetry: any }) {
  const isRed = telemetry.densityStatus === "RED";
  const isYellow = telemetry.densityStatus === "YELLOW";

  const statusColor = isRed
    ? "bg-red-500/20 text-red-400 border-red-500/50"
    : isYellow
    ? "bg-amber-500/20 text-amber-400 border-amber-500/50"
    : "bg-emerald-500/20 text-emerald-400 border-emerald-500/50";

  const capacityPercent = Math.min(
    100,
    Math.round((telemetry.personCount / telemetry.maxCapacity) * 100)
  );

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
          <span>LIVE PASSENGER COUNT</span>
          <Users className="w-4 h-4" />
        </div>
        <div className="text-3xl font-bold font-mono">{telemetry.personCount}</div>
        <div className="w-full bg-slate-800 h-2 rounded-full mt-3 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              isRed ? "bg-red-500" : isYellow ? "bg-amber-500" : "bg-emerald-500"
            }`}
            style={{ width: `${capacityPercent}%` }}
          />
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
          <span>CHOKE-POINT STATUS</span>
          <Activity className="w-4 h-4" />
        </div>
        <div className="mt-1">
          <span className={`inline-block px-3 py-1 rounded-md text-sm font-bold border ${statusColor}`}>
            {telemetry.densityStatus} ZONE
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          Max Safe Limit: {telemetry.maxCapacity} persons
        </p>
      </div>

      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
          <span>INFERENCE SPEED</span>
          <Navigation className="w-4 h-4" />
        </div>
        <div className="text-3xl font-bold font-mono text-blue-400">
          {telemetry.fps} <span className="text-sm font-normal text-slate-400">FPS</span>
        </div>
        <p className="text-xs text-slate-400 mt-2">YOLOv8n (Class 0: Person)</p>
      </div>
    </div>
  );
}