"use client";

import { useEffect, useState } from "react";
import { ArrowRight, RouteOff, Loader2 } from "lucide-react";
import clsx from "clsx";
import { optimizeRoute } from "@/lib/api";
import { OptimizeResponse, TwinNode } from "@/lib/types";

interface OptimizationCardProps {
  nodes: TwinNode[];
  onResult: (result: OptimizeResponse) => void;
  result: OptimizeResponse | null;
}

export default function OptimizationCard({
  nodes,
  onResult,
  result,
}: OptimizationCardProps) {
  const [sourceId, setSourceId] = useState<string>("");
  const [targetId, setTargetId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Whenever the current network changes (a new custom chain was generated,
  // the demo network was restored, or the admin reset the twin), the node
  // IDs we had selected may no longer exist. Re-sync to valid IDs from the
  // *current* node list so we never submit a stale/unknown ID to the API
  // (which previously surfaced as a confusing "network error").
  useEffect(() => {
    const ids = new Set(nodes.map((n) => n.id));
    setSourceId((prev) => (prev && ids.has(prev) ? prev : nodes[0]?.id ?? ""));
    setTargetId((prev) =>
      prev && ids.has(prev) ? prev : nodes[nodes.length - 1]?.id ?? ""
    );
    setError(null);
  }, [nodes]);

  const handleOptimize = async () => {
    if (!sourceId || !targetId || sourceId === targetId) {
      setError("Select two different origin and destination nodes.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const optimize = await optimizeRoute(sourceId, targetId);
      onResult(optimize);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimization failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel panel-amber p-4 flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <span className="flex items-center justify-center w-7 h-7 rounded-full bg-amber-100 text-amber-600 shrink-0">
          <RouteOff size={15} />
        </span>
        <h2 className="text-sm font-semibold text-slate-800">
          Path Comparison &amp; Rerouting
        </h2>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-2">
        <select
          value={sourceId}
          onChange={(e) => setSourceId(e.target.value)}
          className="flex-1 w-full bg-white border border-amber-200 rounded-lg px-2.5 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-300"
        >
          {nodes.map((n) => (
            <option key={n.id} value={n.id}>
              {n.name}
            </option>
          ))}
        </select>
        <ArrowRight size={14} className="text-amber-400 shrink-0" />
        <select
          value={targetId}
          onChange={(e) => setTargetId(e.target.value)}
          className="flex-1 w-full bg-white border border-amber-200 rounded-lg px-2.5 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-300"
        >
          {nodes.map((n) => (
            <option key={n.id} value={n.id}>
              {n.name}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={handleOptimize}
        disabled={loading || nodes.length === 0}
        className={clsx(
          "flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition shadow-sm",
          loading || nodes.length === 0
            ? "bg-slate-100 text-slate-400 cursor-not-allowed"
            : "bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
        )}
      >
        {loading && <Loader2 size={14} className="animate-spin" />}
        {loading ? "Optimizing..." : "Compute Best Route"}
      </button>

      {error && <p className="text-xs text-status-critical">{error}</p>}

      {result && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-400 text-left border-b border-amber-100">
                <th className="py-1.5 font-medium">Route</th>
                <th className="py-1.5 font-medium">Cost</th>
                <th className="py-1.5 font-medium">Transit</th>
                <th className="py-1.5 font-medium">Feasible</th>
              </tr>
            </thead>
            <tbody>
              <RouteRow label="Baseline" tone="nominal" route={result.baseline} />
              <RouteRow label="Disrupted" tone="critical" route={result.disrupted} />
              <RouteRow label="AI Reroute" tone="reroute" route={result.optimized} />
            </tbody>
          </table>

          <div className="grid grid-cols-3 gap-3 mt-4">
            <MiniStat
              label="Time-to-Recovery"
              value={`${result.time_to_recovery_days}d`}
              colorClass="bg-sky-50 text-sky-700"
            />
            <MiniStat
              label="Cost Overhead"
              value={`${result.cost_overhead_pct > 0 ? "+" : ""}${result.cost_overhead_pct}%`}
              colorClass="bg-amber-50 text-amber-700"
            />
            <MiniStat
              label="Time Saved"
              value={`${result.time_saved_days > 0 ? "+" : ""}${result.time_saved_days}d`}
              colorClass={
                result.time_saved_days > 0
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-rose-50 text-rose-700"
              }
            />
          </div>
        </div>
      )}
    </div>
  );
}

function RouteRow({
  label,
  tone,
  route,
}: {
  label: string;
  tone: "nominal" | "critical" | "reroute";
  route: OptimizeResponse["baseline"];
}) {
  const toneColor = {
    nominal: "text-status-nominal",
    critical: "text-status-critical",
    reroute: "text-status-reroute",
  }[tone];

  return (
    <tr className="border-b border-amber-50">
      <td className={clsx("py-2 font-semibold", toneColor)}>{label}</td>
      <td className="py-2 text-slate-700">${route.total_cost.toLocaleString()}</td>
      <td className="py-2 text-slate-700">{route.total_transit_days}d</td>
      <td className="py-2 text-slate-700">{route.feasible ? "Yes" : "No"}</td>
    </tr>
  );
}

function MiniStat({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: string;
  colorClass: string;
}) {
  return (
    <div className={clsx("rounded-lg p-2.5 text-center", colorClass)}>
      <div className="text-sm font-bold tabular-nums">{value}</div>
      <div className="text-[10px] uppercase tracking-wider opacity-70 mt-0.5">
        {label}
      </div>
    </div>
  );
}
