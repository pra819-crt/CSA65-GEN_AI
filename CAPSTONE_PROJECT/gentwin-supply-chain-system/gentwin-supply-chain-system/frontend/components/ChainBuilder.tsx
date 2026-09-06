"use client";

import { useState } from "react";
import { Boxes, Loader2, Sparkles, Undo2 } from "lucide-react";
import clsx from "clsx";
import { generateChain, restoreDefaultNetwork } from "@/lib/api";
import { NetworkResponse } from "@/lib/types";

interface ChainBuilderProps {
  onChainGenerated: (network: NetworkResponse, summary: string) => void;
  onRestoreDefault: (network: NetworkResponse) => void;
}

const EXAMPLE =
  "I run a small electronics business. I source components from a supplier in Shenzhen, " +
  "assemble products at my factory in Chennai, store finished goods in a warehouse in Mumbai, " +
  "and ship to retail partners in Delhi and Bangalore.";

export default function ChainBuilder({
  onChainGenerated,
  onRestoreDefault,
}: ChainBuilderProps) {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSummary, setLastSummary] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const handleGenerate = async () => {
    if (description.trim().length < 10) {
      setError("Tell us a bit more — a couple of sentences works well.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await generateChain(description);
      setLastSummary(result.summary);
      onChainGenerated(result.network, result.summary);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't build a chain from that description."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async () => {
    setRestoring(true);
    setError(null);
    try {
      const network = await restoreDefaultNetwork();
      setLastSummary(null);
      onRestoreDefault(network);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't restore the demo network.");
    } finally {
      setRestoring(false);
    }
  };

  return (
    <div className="panel panel-emerald p-4 flex flex-col gap-3 bg-gradient-to-br from-white to-emerald-50/40">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-7 h-7 rounded-full bg-emerald-100 text-emerald-600 shrink-0">
            <Boxes size={15} />
          </span>
          <h2 className="text-sm font-semibold text-slate-800">
            Use Your Own Supply Chain
          </h2>
        </div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-xs font-medium text-emerald-600 hover:text-emerald-700 hover:underline"
        >
          {expanded ? "Hide" : "Get started →"}
        </button>
      </div>

      {!expanded && (
        <p className="text-xs text-slate-500">
          By default you're exploring a sample global network. Click{" "}
          <span className="text-emerald-600 font-medium">Get started</span> to
          describe your own suppliers, factories, and routes instead.
        </p>
      )}

      {expanded && (
        <>
          <p className="text-xs text-slate-500">
            Describe your suppliers, factories, warehouses, and where you
            ship to — in your own words. We'll turn it into a network you
            can run "what if" simulations on.
          </p>

          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={EXAMPLE}
            rows={4}
            disabled={loading}
            className="w-full resize-none rounded-lg bg-white border border-emerald-200 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:opacity-60"
          />

          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={handleGenerate}
              disabled={loading}
              className={clsx(
                "flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition shadow-sm",
                loading
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white"
              )}
            >
              {loading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Sparkles size={16} />
              )}
              {loading ? "Building your chain..." : "Build My Supply Chain"}
            </button>

            <button
              onClick={handleRestore}
              disabled={restoring}
              title="Go back to the sample global network"
              className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm bg-white hover:bg-emerald-50 border border-emerald-200 text-emerald-700 transition disabled:opacity-50"
            >
              {restoring ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Undo2 size={14} />
              )}
              Use sample instead
            </button>
          </div>

          {error && <p className="text-xs text-status-critical">{error}</p>}

          {lastSummary && (
            <div className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
              <span className="font-semibold text-emerald-700">Built: </span>
              {lastSummary}
            </div>
          )}
        </>
      )}
    </div>
  );
}
