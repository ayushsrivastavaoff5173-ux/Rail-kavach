"use client";

import React from "react";
import { Video } from "lucide-react";

export default function CameraFeed({
  telemetry,
  isSimulating,
  isConnected,
}: {
  telemetry: any;
  isSimulating: boolean;
  isConnected: boolean;
}) {
  const isRed = telemetry.densityStatus === "RED";
  const isYellow = telemetry.densityStatus === "YELLOW";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Video className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold">CAM-01: {telemetry.zone}</span>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {telemetry.fps} FPS | Source: {telemetry.activeSource}
        </span>
      </div>

      <div className="relative aspect-video bg-slate-950 flex flex-col items-center justify-center">
        {!isSimulating && isConnected ? (
          <img
            src="http://localhost:8000/video_feed"
            alt="YOLOv8 Live Stream"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="text-center p-6">
            <div className="inline-flex p-3 rounded-full bg-slate-900 border border-slate-800 mb-3">
              <Video className="w-8 h-8 text-slate-500" />
            </div>
            <p className="text-sm text-slate-300 font-medium">
              Simulation Mode Active ({telemetry.activeSource})
            </p>
            <p className="text-xs text-slate-500 mt-1 max-w-md">
              Connect FastAPI Backend on port 8000 to view live YOLOv8 bounding-box stream.
            </p>
          </div>
        )}

        <div className="absolute top-3 left-3 px-2.5 py-1 rounded bg-slate-950/80 border border-slate-800 text-xs font-mono flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isRed ? "bg-red-500" : isYellow ? "bg-amber-500" : "bg-emerald-500"
            }`}
          />
          COUNT: {telemetry.personCount} / {telemetry.maxCapacity}
        </div>
      </div>
    </div>
  );
}