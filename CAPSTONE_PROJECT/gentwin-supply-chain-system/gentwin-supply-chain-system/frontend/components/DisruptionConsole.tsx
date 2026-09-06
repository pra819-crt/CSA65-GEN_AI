"use client";

import { useState } from "react";
import { Send, Loader2, Sparkles, Wand2 } from "lucide-react";
import clsx from "clsx";
import { simulateDisruption, suggestScenarios } from "@/lib/api";
import { ScenarioSuggestion, SimulateResponse } from "@/lib/types";

interface DisruptionConsoleProps {
  onResult: (result: SimulateResponse) => void;
}

const PRESETS: { emoji: string; label: string; prompt: string; tint: string }[] = [
  {
    emoji: "🔴",
    label: "Red Sea Shipping Vessel Delays",
    tint: "bg-rose-50 hover:bg-rose-100 border-rose-200 text-rose-700",
    prompt:
      "A series of attacks on commercial vessels in the Red Sea has forced carriers to reroute around the Cape of Good Hope, adding significant transit time and cost to Asia-Europe sea lanes for the next several weeks.",
  },
  {
    emoji: "🟠",
    label: "Taiwan Semiconductor Factory Outage",
    tint: "bg-orange-50 hover:bg-orange-100 border-orange-200 text-orange-700",
    prompt:
      "A major earthquake has caused an unplanned outage at a semiconductor factory cluster near Shenzhen, halting component production and creating a two-week backlog for downstream electronics manufacturing.",
  },
  {
    emoji: "🟡",
    label: "Port of LA Dockworker Strike",
    tint: "bg-amber-50 hover:bg-amber-100 border-amber-200 text-amber-700",
    prompt:
      "Dockworkers at the Port of Los Angeles have gone on strike over new contract terms, causing container backlogs and halting inbound/outbound cargo processing for an estimated 8-10 days.",
  },
];

const RISK_STYLE: Record<string, { emoji: string; tint: string }> = {
  Low: { emoji: "🟡", tint: "bg-amber-50 hover:bg-amber-100 border-amber-200 text-amber-700" },
  Medium: { emoji: "🟠", tint: "bg-orange-50 hover:bg-orange-100 border-orange-200 text-orange-700" },
  High: { emoji: "🔴", tint: "bg-rose-50 hover:bg-rose-100 border-rose-200 text-rose-700" },
};

const LOADING_STEPS = [
  "Ingesting disruption prompt...",
  "Snapshotting Digital Twin network state...",
  "Querying Gemini for structured impact analysis...",
  "Applying disruption weights to the twin...",
];

export default function DisruptionConsole({ onResult }: DisruptionConsoleProps) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [aiScenarios, setAiScenarios] = useState<ScenarioSuggestion[]>([]);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestError, setSuggestError] = useState<string | null>(null);

  const runSimulation = async (submittedPrompt: string) => {
    if (submittedPrompt.trim().length < 5) {
      setError("Please provide a more detailed disruption scenario.");
      return;
    }
    setLoading(true);
    setError(null);
    setStepIndex(0);

    const stepTimer = setInterval(() => {
      setStepIndex((prev) => Math.min(prev + 1, LOADING_STEPS.length - 1));
    }, 700);

    try {
      const result = await simulateDisruption(submittedPrompt);
      onResult(result);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Simulation failed unexpectedly."
      );
    } finally {
      clearInterval(stepTimer);
      setLoading(false);
    }
  };

  const handleGetAiSuggestions = async () => {
    setSuggesting(true);
    setSuggestError(null);
    try {
      const result = await suggestScenarios();
      setAiScenarios(result.scenarios);
    } catch (err) {
      setSuggestError(
        err instanceof Error ? err.message : "Could not fetch AI suggestions."
      );
    } finally {
      setSuggesting(false);
    }
  };

  return (
    <div className="panel panel-indigo p-4 flex flex-col gap-3 bg-gradient-to-br from-white to-indigo-50/40">
      <div className="flex items-center gap-2">
        <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-100 text-indigo-600 shrink-0">
          <Sparkles size={15} />
        </span>
        <h2 className="text-sm font-semibold text-slate-800">
          Disruption Simulator
        </h2>
      </div>
      <p className="text-xs text-slate-500 -mt-2">
        Pick a suggestion below, or describe your own "what if" scenario in
        plain English.
      </p>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="e.g. 'Suez Canal blocked for 12 days, high risk of port backlog in Europe.'"
        rows={4}
        disabled={loading}
        className="w-full resize-none rounded-lg bg-white border border-indigo-200 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 disabled:opacity-60"
      />

      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase tracking-wider text-slate-400">
            {aiScenarios.length > 0 ? "AI-suggested for your network" : "Quick presets"}
          </span>
          <button
            onClick={handleGetAiSuggestions}
            disabled={suggesting || loading}
            className="text-[11px] flex items-center gap-1 font-medium text-indigo-600 hover:text-indigo-700 hover:underline disabled:opacity-50 disabled:no-underline"
          >
            {suggesting ? (
              <Loader2 size={11} className="animate-spin" />
            ) : (
              <Wand2 size={11} />
            )}
            {suggesting ? "Thinking..." : "Suggest scenarios for my network"}
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {(aiScenarios.length > 0
            ? aiScenarios.map((s) => ({
                emoji: RISK_STYLE[s.risk_level]?.emoji ?? "⚪",
                tint: RISK_STYLE[s.risk_level]?.tint ?? "bg-slate-50 border-slate-200 text-slate-700",
                label: s.title,
                prompt: s.prompt,
              }))
            : PRESETS
          ).map((item, idx) => (
            <button
              key={idx}
              disabled={loading}
              onClick={() => setPrompt(item.prompt)}
              className={clsx(
                "text-xs px-2.5 py-1.5 rounded-full border font-medium transition disabled:opacity-50",
                item.tint
              )}
            >
              {item.emoji} {item.label}
            </button>
          ))}
        </div>

        {suggestError && (
          <p className="text-[11px] text-status-critical">{suggestError}</p>
        )}
      </div>

      <button
        onClick={() => runSimulation(prompt)}
        disabled={loading}
        className={clsx(
          "flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition shadow-sm",
          loading
            ? "bg-slate-100 text-slate-400 cursor-not-allowed"
            : "bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white"
        )}
      >
        {loading ? (
          <Loader2 size={16} className="animate-spin" />
        ) : (
          <Send size={16} />
        )}
        {loading ? "Simulating..." : "Run Disruption Simulation"}
      </button>

      {loading && (
        <div className="mt-1 space-y-1.5">
          {LOADING_STEPS.map((step, idx) => (
            <div
              key={step}
              className={clsx(
                "text-xs flex items-center gap-2 transition-opacity",
                idx <= stepIndex ? "opacity-100 text-slate-600" : "opacity-30 text-slate-400"
              )}
            >
              <span
                className={clsx(
                  "w-1.5 h-1.5 rounded-full",
                  idx <= stepIndex ? "bg-indigo-500" : "bg-slate-200"
                )}
              />
              {step}
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-xs text-status-critical">{error}</p>}
    </div>
  );
}
