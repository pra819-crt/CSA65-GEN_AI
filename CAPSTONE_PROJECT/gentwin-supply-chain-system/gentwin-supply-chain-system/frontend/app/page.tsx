"use client";

import { useCallback, useEffect, useState } from "react";
import AuthGuard from "@/components/AuthGuard";
import Header from "@/components/Header";
import NetworkMap from "@/components/NetworkMap";
import ChainBuilder from "@/components/ChainBuilder";
import DisruptionConsole from "@/components/DisruptionConsole";
import ImpactMetrics from "@/components/ImpactMetrics";
import OptimizationCard from "@/components/OptimizationCard";
import { fetchNetwork } from "@/lib/api";
import {
  DisruptionAnalysis,
  NetworkResponse,
  OptimizeResponse,
  SimulateResponse,
} from "@/lib/types";
import { useAuth } from "@/context/AuthContext";

function Dashboard() {
  const { isAuthenticated } = useAuth();
  const [network, setNetwork] = useState<NetworkResponse>({ nodes: [], edges: [] });
  const [analysis, setAnalysis] = useState<DisruptionAnalysis | null>(null);
  const [optimize, setOptimize] = useState<OptimizeResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [chainSummary, setChainSummary] = useState<string | null>(null);

  const loadNetwork = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await fetchNetwork();
      setNetwork(data);
    } catch (err) {
      setLoadError(
        err instanceof Error
          ? err.message
          : "Failed to load network state from backend."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadNetwork();
    }
  }, [isAuthenticated, loadNetwork]);

  const handleSimulateResult = (result: SimulateResponse) => {
    setAnalysis(result.analysis);
    setNetwork(result.network);
    setOptimize(null);
  };

  const handleOptimizeResult = (result: OptimizeResponse) => {
    setOptimize(result);
  };

  const handleReset = () => {
    setAnalysis(null);
    setOptimize(null);
    loadNetwork();
  };

  const handleChainGenerated = (newNetwork: NetworkResponse, summary: string) => {
    setNetwork(newNetwork);
    setChainSummary(summary);
    setAnalysis(null);
    setOptimize(null);
  };

  const handleRestoreDefault = (newNetwork: NetworkResponse) => {
    setNetwork(newNetwork);
    setChainSummary(null);
    setAnalysis(null);
    setOptimize(null);
  };

  return (
    <main className="min-h-screen pb-10">
      <Header nodes={network.nodes} edges={network.edges} onReset={handleReset} />

      {loadError && (
        <div className="mx-4 mt-4 panel border-status-critical/30 px-4 py-3 text-sm text-status-critical">
          {loadError}. Make sure the FastAPI backend is running at{" "}
          <code className="text-xs bg-base-800 px-1.5 py-0.5 rounded">
            http://localhost:8000
          </code>
          .
        </div>
      )}

      <div className="mx-4 mt-4">
        <ChainBuilder
          onChainGenerated={handleChainGenerated}
          onRestoreDefault={handleRestoreDefault}
        />
      </div>

      <div className="mx-4 mt-4 grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 flex flex-col gap-4">
          {loading ? (
            <div className="panel p-10 text-center text-sm text-slate-400">
              Loading Digital Twin network...
            </div>
          ) : (
            <NetworkMap
              nodes={network.nodes}
              edges={network.edges}
              optimizedPathEdgeIds={optimize?.optimized.edge_ids ?? []}
            />
          )}

          {chainSummary && !analysis && (
            <div className="panel p-4">
              <h2 className="text-sm font-semibold text-status-nominal mb-1">
                Your Supply Chain
              </h2>
              <p className="text-xs text-slate-600 leading-relaxed">{chainSummary}</p>
            </div>
          )}

          {analysis && (
            <div className="panel p-4">
              <h2 className="text-sm font-semibold text-slate-900 mb-1">
                {analysis.scenario_title}
              </h2>
              <p className="text-xs text-slate-600 leading-relaxed">
                {analysis.executive_summary}
              </p>
            </div>
          )}

          <OptimizationCard
            nodes={network.nodes}
            result={optimize}
            onResult={handleOptimizeResult}
          />
        </div>

        <div className="flex flex-col gap-4">
          <DisruptionConsole onResult={handleSimulateResult} />
          <ImpactMetrics analysis={analysis} optimize={optimize} />
        </div>
      </div>
    </main>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <Dashboard />
    </AuthGuard>
  );
}
