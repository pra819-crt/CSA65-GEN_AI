"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import clsx from "clsx";
import { BarChart3 } from "lucide-react";
import { DisruptionAnalysis, OptimizeResponse } from "@/lib/types";

interface ImpactMetricsProps {
  analysis: DisruptionAnalysis | null;
  optimize: OptimizeResponse | null;
}

export default function ImpactMetrics({ analysis, optimize }: ImpactMetricsProps) {
  const severity = analysis?.overall_severity_score ?? 0;
  const costIncreasePct = analysis
    ? Math.round((analysis.cost_multiplier - 1) * 1000) / 10
    : 0;
  const delayDays = optimize
    ? Math.round(
        (optimize.disrupted.total_transit_days - optimize.baseline.total_transit_days) * 10
      ) / 10
    : 0;

  const chartData = optimize
    ? [
        {
          name: "Cost ($)",
          Baseline: optimize.baseline.total_cost,
          Disrupted: optimize.disrupted.total_cost,
          Optimized: optimize.optimized.total_cost,
        },
      ]
    : [];

  return (
    <div className="panel panel-rose p-4 flex flex-col gap-4 bg-gradient-to-br from-white to-rose-50/30">
      <div className="flex items-center gap-2">
        <span className="flex items-center justify-center w-7 h-7 rounded-full bg-rose-100 text-rose-600 shrink-0">
          <BarChart3 size={15} />
        </span>
        <h2 className="text-sm font-semibold text-slate-800">Impact Analysis</h2>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <KpiCard
          label="Severity Score"
          value={`${severity}`}
          suffix="/100"
          tone={severity >= 70 ? "critical" : severity >= 40 ? "warning" : "nominal"}
          gauge={severity}
        />
        <KpiCard
          label="Cost Increase"
          value={`${costIncreasePct > 0 ? "+" : ""}${costIncreasePct}`}
          suffix="%"
          tone={costIncreasePct > 50 ? "critical" : costIncreasePct > 15 ? "warning" : "nominal"}
        />
        <KpiCard
          label="Delay Duration"
          value={`${delayDays > 0 ? "+" : ""}${delayDays}`}
          suffix=" days"
          tone={delayDays > 5 ? "critical" : delayDays > 1 ? "warning" : "nominal"}
        />
      </div>

      {optimize && (
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#fee2e2" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{
                  background: "#ffffff",
                  border: "1px solid #fecdd3",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="Baseline" fill="#059669" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Disrupted" fill="#e11d48" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Optimized" fill="#0891b2" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {analysis && (
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Mitigation Playbook
          </h3>
          <ul className="space-y-1.5">
            {analysis.risk_mitigation_recommendations.map((rec, idx) => (
              <li
                key={idx}
                className="text-xs text-indigo-900 flex items-start gap-2 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2"
              >
                <span className="text-indigo-500 font-bold">{idx + 1}.</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!analysis && !optimize && (
        <p className="text-xs text-slate-400 text-center py-6">
          Run a disruption simulation to see impact metrics.
        </p>
      )}
    </div>
  );
}

function KpiCard({
  label,
  value,
  suffix,
  tone,
  gauge,
}: {
  label: string;
  value: string;
  suffix?: string;
  tone: "nominal" | "warning" | "critical";
  gauge?: number;
}) {
  const styles = {
    nominal: { bg: "bg-emerald-50", text: "text-emerald-700", bar: "bg-emerald-500" },
    warning: { bg: "bg-amber-50", text: "text-amber-700", bar: "bg-amber-500" },
    critical: { bg: "bg-rose-50", text: "text-rose-700", bar: "bg-rose-500" },
  }[tone];

  return (
    <div className={clsx("rounded-xl p-3 flex flex-col gap-1.5", styles.bg)}>
      <span className="text-[10px] uppercase tracking-wider text-slate-500">
        {label}
      </span>
      <span className={clsx("text-xl font-bold tabular-nums", styles.text)}>
        {value}
        {suffix && (
          <span className="text-xs text-slate-400 font-normal">{suffix}</span>
        )}
      </span>
      {gauge !== undefined && (
        <div className="w-full h-1.5 bg-white rounded-full overflow-hidden">
          <div
            className={clsx("h-full rounded-full transition-all", styles.bar)}
            style={{ width: `${Math.min(100, Math.max(0, gauge))}%` }}
          />
        </div>
      )}
    </div>
  );
}
