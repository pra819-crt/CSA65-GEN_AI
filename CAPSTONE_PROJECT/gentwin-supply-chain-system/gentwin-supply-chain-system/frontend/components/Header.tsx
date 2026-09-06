"use client";

import { useState } from "react";
import { Activity, AlertTriangle, RotateCcw, Loader2, LogOut, UserCircle2, Boxes } from "lucide-react";
import clsx from "clsx";
import { resetNetwork } from "@/lib/api";
import { TwinEdge, TwinNode } from "@/lib/types";
import { useAuth } from "@/context/AuthContext";

interface HeaderProps {
  nodes: TwinNode[];
  edges: TwinEdge[];
  onReset: () => void;
}

export default function Header({ nodes, edges, onReset }: HeaderProps) {
  const { user, logout } = useAuth();
  const [resetting, setResetting] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);

  const disruptedEdges = edges.filter((e) => e.is_disrupted);
  const isDisrupted = disruptedEdges.length > 0;
  const isAdmin = user?.role === "admin";

  const avgLatencyDelayPct =
    disruptedEdges.length > 0
      ? Math.round(
          ((disruptedEdges.reduce((sum, e) => sum + e.risk_factor, 0) /
            disruptedEdges.length -
            1) *
            100) *
            100
        ) / 100
      : 0;

  const handleReset = async () => {
    setResetting(true);
    setResetError(null);
    try {
      await resetNetwork();
      onReset();
    } catch (err) {
      setResetError(
        err instanceof Error ? err.message : "Failed to reset network state."
      );
    } finally {
      setResetting(false);
    }
  };

  return (
    <header className="mx-4 mt-4 px-6 py-5 rounded-2xl shadow-lg flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between bg-gradient-to-r from-indigo-600 via-violet-600 to-fuchsia-500 text-white relative overflow-hidden">
      <div className="absolute inset-0 opacity-10 pointer-events-none [background-image:radial-gradient(circle_at_20%_20%,white,transparent_35%),radial-gradient(circle_at_80%_60%,white,transparent_30%)]" />

      <div className="flex items-center gap-4 relative">
        <span className="hidden sm:flex items-center justify-center w-10 h-10 rounded-xl bg-white/15 backdrop-blur-sm shrink-0">
          <Boxes size={20} />
        </span>
        <div>
          <h1 className="text-lg font-bold tracking-tight">
            GenTwin{" "}
            <span className="text-white/70 font-normal">
              — Supply Chain Resilience System
            </span>
          </h1>
          <p className="text-xs text-white/70 mt-0.5">
            Generative AI &amp; Digital Twin-Based Disruption Management
          </p>
        </div>

        <div
          className={clsx(
            "badge backdrop-blur-sm",
            isDisrupted
              ? "bg-rose-400/20 text-rose-50 border border-rose-200/40"
              : "bg-emerald-400/20 text-emerald-50 border border-emerald-200/40"
          )}
        >
          {isDisrupted ? (
            <AlertTriangle size={14} className="animate-pulseSlow" />
          ) : (
            <Activity size={14} />
          )}
          {isDisrupted ? "Disruption Active" : "System Nominal"}
        </div>
      </div>

      <div className="flex items-center gap-6 flex-wrap relative">
        <MetricPill label="Active Nodes" value={nodes.length.toString()} />
        <MetricPill
          label="Disrupted Routes"
          value={disruptedEdges.length.toString()}
          tone={disruptedEdges.length > 0 ? "critical" : "nominal"}
        />
        <MetricPill
          label="Avg Latency Delay"
          value={`${avgLatencyDelayPct > 0 ? "+" : ""}${avgLatencyDelayPct}%`}
          tone={avgLatencyDelayPct > 0 ? "warning" : "nominal"}
        />

        {isAdmin && (
          <button
            onClick={handleReset}
            disabled={resetting}
            title="Reset network state (admin only)"
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-sm text-white transition disabled:opacity-50"
          >
            {resetting ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <RotateCcw size={14} />
            )}
            Reset Network State
          </button>
        )}

        <div className="flex items-center gap-3 pl-3 border-l border-white/20">
          <div className="flex items-center gap-1.5">
            <span className="flex items-center justify-center w-7 h-7 rounded-full bg-white/15">
              <UserCircle2 size={16} />
            </span>
            <div className="text-left">
              <div className="text-xs font-semibold leading-tight">
                {user?.full_name || user?.username}
              </div>
              <div
                className={clsx(
                  "text-[10px] uppercase tracking-wider leading-tight",
                  isAdmin ? "text-amber-200" : "text-white/60"
                )}
              >
                {user?.role}
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg bg-white/10 hover:bg-rose-400/30 border border-white/20 text-xs text-white transition"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>

      {resetError && (
        <p className="text-xs text-rose-100 bg-rose-500/30 rounded px-2 py-1 lg:absolute lg:right-6 lg:-bottom-8">
          {resetError}
        </p>
      )}
    </header>
  );
}

function MetricPill({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "critical" | "warning" | "nominal";
}) {
  const toneClass = {
    default: "text-white",
    critical: "text-rose-200",
    warning: "text-amber-200",
    nominal: "text-emerald-200",
  }[tone];

  return (
    <div className="text-right">
      <div className={clsx("text-sm font-bold tabular-nums", toneClass)}>
        {value}
      </div>
      <div className="text-[10px] uppercase tracking-wider text-white/60">
        {label}
      </div>
    </div>
  );
}
