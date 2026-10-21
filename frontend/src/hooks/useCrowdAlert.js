"use client";

import { useState, useEffect, useRef, useCallback } from "react";

const INITIAL_TELEMETRY = {
  timestamp: "21:30:00",
  zone: "FOB-1 (Charbagh North)",
  personCount: 18,
  maxCapacity: 45,
  densityStatus: "GREEN",
  fps: 42.5,
  evacuationRoute: "All clear. Normal passenger flow on Foot-Over-Bridge 1.",
  activeSource: "normal_flow.mp4",
};

export function useCrowdAlert(wsUrl = "ws://localhost:8000/ws/telemetry") {
  const [telemetry, setTelemetry] = useState(INITIAL_TELEMETRY);
  const [isConnected, setIsConnected] = useState(false);
  const [isSimulating, setIsSimulating] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [alertLogs, setAlertLogs] = useState([
    { time: "21:30:00", level: "INFO", msg: "RailKavach Command Center initialized." },
  ]);

  const wsRef = useRef(null);
  const lastSpokenRef = useRef(0);

  const addLog = useCallback((level, msg) => {
    const time = new Date().toLocaleTimeString();
    setAlertLogs((prev) => [{ time, level, msg }, ...prev.slice(0, 14)]);
  }, []);

  const triggerPAAnnouncement = useCallback(
    (status, count) => {
      if (!audioEnabled || typeof window === "undefined" || !("speechSynthesis" in window)) return;

      const now = Date.now();
      if (now - lastSpokenRef.current < 12000) return;

      if (status === "RED") {
        lastSpokenRef.current = now;
        window.speechSynthesis.cancel();

        const hindiMsg = new SpeechSynthesisUtterance(
          "Yaatri kripya dhyan dein! Foot over bridge ek par bheed adhik hai. Kripya suraksha ke liye bridge do ka upyog karein."
        );
        hindiMsg.lang = "hi-IN";
        hindiMsg.rate = 0.95;

        const engMsg = new SpeechSynthesisUtterance(
          `Attention please! High crowd alert on Foot Over Bridge 1 with ${count} passengers. Please divert to Bridge 2 immediately. RPF team alerted.`
        );
        engMsg.lang = "en-IN";
        engMsg.rate = 1.0;

        window.speechSynthesis.speak(hindiMsg);
        window.speechSynthesis.speak(engMsg);

        addLog("CRITICAL", `PA Broadcast Triggered (Count: ${count}) + RPF SOS Dispatched`);
      }
    },
    [audioEnabled, addLog]
  );

  useEffect(() => {
    if (isSimulating) {
      if (wsRef.current) wsRef.current.close();
      setIsConnected(false);
      return;
    }

    let ws;
    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        addLog("INFO", "Connected to YOLOv8 FastAPI Telemetry Stream.");
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setTelemetry(data);
        if (data.densityStatus === "RED") {
          triggerPAAnnouncement("RED", data.personCount);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        addLog("WARN", "Backend WebSocket disconnected. Switched to standby.");
      };
    } catch (err) {
      console.error("WS Error:", err);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [wsUrl, isSimulating, triggerPAAnnouncement, addLog]);

  const simulateScenario = (mode) => {
    setIsSimulating(true);
    const time = new Date().toLocaleTimeString();

    if (mode === "GREEN") {
      setTelemetry({
        timestamp: time,
        zone: "FOB-1 (Charbagh North)",
        personCount: 16,
        maxCapacity: 45,
        densityStatus: "GREEN",
        fps: 44.2,
        evacuationRoute: "All clear. Normal passenger flow on FOB-1.",
        activeSource: "normal_flow.mp4",
      });
      addLog("INFO", "Switched to Normal Flow scenario (Green).");
    } else if (mode === "YELLOW") {
      setTelemetry({
        timestamp: time,
        zone: "FOB-1 (Charbagh North)",
        personCount: 34,
        maxCapacity: 45,
        densityStatus: "YELLOW",
        fps: 41.8,
        evacuationRoute: "Moderate crowd buildup. Standby gate control at Platform 1.",
        activeSource: "moderate_crowd.mp4",
      });
      addLog("WARN", "Crowd threshold crossing 75% on FOB-1 (Yellow).");
    } else if (mode === "RED") {
      setTelemetry({
        timestamp: time,
        zone: "FOB-1 (Charbagh North)",
        personCount: 58,
        maxCapacity: 45,
        densityStatus: "RED",
        fps: 39.5,
        evacuationRoute: "CRITICAL SURGE! Diverting Platform 1 passengers to FOB-2 via East Escalator.",
        activeSource: "rush_surge.mp4",
      });
      triggerPAAnnouncement("RED", 58);
    }
  };

  return {
    telemetry,
    isConnected,
    isSimulating,
    setIsSimulating,
    audioEnabled,
    setAudioEnabled,
    alertLogs,
    simulateScenario,
  };
}