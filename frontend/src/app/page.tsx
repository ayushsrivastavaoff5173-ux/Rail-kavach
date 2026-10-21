"use client";

import React from "react";
import { useCrowdAlert } from "@/hooks/useCrowdAlert";
import AlertBanner from "@/components/AlertBanner";
import CameraFeed from "@/components/CameraFeed";
import TelemetryGauge from "@/components/TelemetryGauge";
import StationMap from "@/components/StationMap";
import { ShieldAlert, Volume2, VolumeX, Radio, Terminal } from "lucide-react";

export default function RailKavachDashboard() {
  const {
    telemetry,
    isConnected,
    isSimulating,
    setIsSimulating,
    audioEnabled,
    setAudioEnabled,
    alertLogs,
    simulateScenario,
  } = useCrowdAlert();

  const isRed = telemetry.densityStatus === "RED";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6 font-sans">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-red-600/20 border border-red-500/40 rounded-lg">
            <ShieldAlert className="w-7 h-7 text-red-500" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">RailKavach</h1>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                LKO-CHARBAGH-NODE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Autonomous Railway Platform & Stampede Early Warning System
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1 gap-1">
            <span className="text-xs text-slate-400 px-2">Test:</span>
            <button onClick={() => simulateScenario("GREEN")} className="px-2.5 py-1 text-xs font-medium rounded bg-emerald-600/20 text-emerald-400">
              Normal
            </button>
            <button onClick={() => simulateScenario("YELLOW")} className="px-2.5 py-1 text-xs font-medium rounded bg-amber-600/20 text-amber-400">
              Moderate
            </button>
            <button onClick={() => simulateScenario("RED")} className="px-2.5 py-1 text-xs font-medium rounded bg-red-600/20 text-red-400">
              Surge (SOS)
            </button>
          </div>

          <button
            onClick={() => setIsSimulating(!isSimulating)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border bg-slate-900 border-slate-800 text-slate-300"
          >
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            {isSimulating ? "Simulating" : isConnected ? "Live WS" : "Disconnected"}
          </button>

          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${
              audioEnabled ? "bg-blue-600/20 border-blue-500 text-blue-300" : "bg-slate-900 border-slate-800 text-slate-400"
            }`}
          >
            {audioEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            {audioEnabled ? "PA Audio: ON" : "Enable PA Audio"}
          </button>
        </div>
      </header>

      <AlertBanner isRed={isRed} evacuationRoute={telemetry.evacuationRoute} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 flex flex-col gap-6">
          <CameraFeed telemetry={telemetry} isSimulating={isSimulating} isConnected={isConnected} />
          <TelemetryGauge telemetry={telemetry} />
        </div>

        <div className="lg:col-span-5 flex flex-col gap-6">
          <StationMap telemetry={telemetry} />

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex-1">
            <h3 className="text-sm font-semibold flex items-center gap-2 mb-3">
              <Terminal className="w-4 h-4 text-amber-400" />
              Closed-Loop Intervention Log
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto font-mono text-xs">
              {alertLogs.map((log: any, index: number) => (
                <div key={index} className="p-2 rounded bg-slate-950 border border-slate-800 flex items-start gap-2">
                  <span className="text-slate-500 shrink-0">[{log.time}]</span>
                  <span className={log.level === "CRITICAL" ? "text-red-400 font-semibold" : log.level === "WARN" ? "text-amber-400" : "text-emerald-400"}>
                    {log.msg}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}