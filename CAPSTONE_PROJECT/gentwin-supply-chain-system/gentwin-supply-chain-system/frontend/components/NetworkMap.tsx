"use client";

import { useMemo, useState } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  Line,
} from "react-simple-maps";
import { TwinEdge, TwinNode } from "@/lib/types";
import { Globe2 } from "lucide-react";
import clsx from "clsx";

interface NetworkMapProps {
  nodes: TwinNode[];
  edges: TwinEdge[];
  optimizedPathEdgeIds?: string[];
}

const WORLD_ATLAS_URL =
  "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const CATEGORY_SHAPE: Record<string, "circle" | "square" | "diamond"> = {
  Port: "circle",
  Factory: "square",
  Hub: "diamond",
  Supplier: "circle",
  Warehouse: "square",
  Retailer: "diamond",
};

// Minimum on-screen pixel distance (in projected map units) below which
// we consider two node labels "too close" and hide the second one rather
// than let the text overlap into an unreadable blob.
const LABEL_COLLISION_DISTANCE = 3.2; // degrees, roughly proportional to zoom

export default function NetworkMap({
  nodes,
  edges,
  optimizedPathEdgeIds = [],
}: NetworkMapProps) {
  const [hoveredNode, setHoveredNode] = useState<TwinNode | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<TwinEdge | null>(null);
  const [cursor, setCursor] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [mapReady, setMapReady] = useState(false);

  const nodeById = useMemo(() => {
    const map = new Map<string, TwinNode>();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);

  const optimizedSet = useMemo(
    () => new Set(optimizedPathEdgeIds),
    [optimizedPathEdgeIds]
  );

  const { center, zoom } = useMemo(() => {
    if (nodes.length === 0) return { center: [10, 20] as [number, number], zoom: 1 };
    const lats = nodes.map((n) => n.lat);
    const lngs = nodes.map((n) => n.lng);
    const midLat = (Math.min(...lats) + Math.max(...lats)) / 2;
    const midLng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
    const spanLat = Math.max(...lats) - Math.min(...lats);
    const spanLng = Math.max(...lngs) - Math.min(...lngs);
    const span = Math.max(spanLat, spanLng, 8);
    const computedZoom = Math.min(6, Math.max(1, 90 / span));
    return { center: [midLng, midLat] as [number, number], zoom: computedZoom };
  }, [nodes]);

  // Decide which nodes get a permanent on-map label vs. name-on-hover only,
  // so labels never overlap into unreadable merged text. A node's label is
  // suppressed if it sits closer than the collision threshold (adjusted for
  // current zoom) to another node that was already given a label.
  const labeledNodeIds = useMemo(() => {
    const threshold = LABEL_COLLISION_DISTANCE / zoom;
    const placed: TwinNode[] = [];
    const visible = new Set<string>();
    // Larger networks get noisier fast — cap how many static labels we
    // ever draw, favoring readability over showing every single name.
    const maxLabels = nodes.length > 14 ? 0 : 16;

    for (const node of nodes) {
      if (placed.length >= maxLabels) break;
      const tooClose = placed.some(
        (p) =>
          Math.abs(p.lat - node.lat) < threshold &&
          Math.abs(p.lng - node.lng) < threshold
      );
      if (!tooClose) {
        placed.push(node);
        visible.add(node.id);
      }
    }
    return visible;
  }, [nodes, zoom]);

  return (
    <div className="panel panel-sky p-4 relative">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-7 h-7 rounded-full bg-sky-100 text-sky-600 shrink-0">
            <Globe2 size={15} />
          </span>
          <h2 className="text-sm font-semibold text-slate-800">
            Global Supply Network
          </h2>
        </div>
        <Legend />
      </div>

      <div
        className="relative w-full overflow-hidden rounded-xl bg-gradient-to-b from-sky-50 to-blue-50 border border-sky-100"
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          setCursor({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        }}
      >
        <ComposableMap
          projection="geoEqualEarth"
          projectionConfig={{ center, scale: 160 * zoom }}
          width={900}
          height={460}
          style={{ width: "100%", height: "420px" }}
        >
          <Geographies geography={WORLD_ATLAS_URL}>
            {({ geographies }) => {
              if (!mapReady && geographies.length > 0) setMapReady(true);
              return geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="#dbeafe"
                  stroke="#93c5fd"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: "none" },
                    hover: { outline: "none", fill: "#bfdbfe" },
                    pressed: { outline: "none" },
                  }}
                />
              ));
            }}
          </Geographies>

          {edges.map((edge) => {
            const src = nodeById.get(edge.source);
            const tgt = nodeById.get(edge.target);
            if (!src || !tgt) return null;

            const isOptimized = optimizedSet.has(edge.id);
            const stroke = isOptimized
              ? "#0891b2"
              : edge.is_disrupted
              ? "#e11d48"
              : "#059669";
            const dash = edge.mode === "Air" ? "4 3" : undefined;

            return (
              <Line
                key={edge.id}
                from={[src.lng, src.lat]}
                to={[tgt.lng, tgt.lat]}
                stroke={stroke}
                strokeWidth={isOptimized ? 2.75 : edge.is_disrupted ? 2.25 : 1.5}
                strokeDasharray={dash}
                strokeOpacity={isOptimized ? 1 : edge.is_disrupted ? 0.95 : 0.65}
                onMouseEnter={() => setHoveredEdge(edge)}
                onMouseLeave={() => setHoveredEdge(null)}
                style={{ cursor: "pointer" }}
              />
            );
          })}

          {nodes.map((node, idx) => {
            const color =
              node.current_status === "Disrupted"
                ? "#e11d48"
                : node.current_status === "Degraded"
                ? "#d97706"
                : "#059669";
            const shape = CATEGORY_SHAPE[node.category] ?? "circle";
            const showLabel = labeledNodeIds.has(node.id);
            // Alternate labels above/below the marker so two labeled nodes
            // that are still reasonably close don't stack directly on top
            // of one another either.
            const labelUp = idx % 2 === 0;

            return (
              <Marker
                key={node.id}
                coordinates={[node.lng, node.lat]}
                onMouseEnter={() => setHoveredNode(node)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ default: { cursor: "pointer" } }}
              >
                {shape === "circle" && (
                  <circle r={5.5} fill={color} stroke="#ffffff" strokeWidth={1.5} />
                )}
                {shape === "square" && (
                  <rect
                    x={-4.5}
                    y={-4.5}
                    width={9}
                    height={9}
                    fill={color}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                  />
                )}
                {shape === "diamond" && (
                  <rect
                    x={-4.5}
                    y={-4.5}
                    width={9}
                    height={9}
                    fill={color}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                    transform="rotate(45)"
                  />
                )}
                {showLabel && (
                  <g style={{ pointerEvents: "none" }}>
                    <rect
                      x={2}
                      y={labelUp ? -18 : 6}
                      width={Math.min(90, node.name.length * 4.6 + 8)}
                      height={13}
                      rx={4}
                      fill="#ffffff"
                      fillOpacity={0.85}
                    />
                    <text
                      x={6}
                      y={labelUp ? -8 : 16}
                      fontSize={9}
                      fontWeight={500}
                      fill="#1e3a5f"
                    >
                      {node.name.split(" ").slice(0, 2).join(" ")}
                    </text>
                  </g>
                )}
              </Marker>
            );
          })}
        </ComposableMap>

        {!mapReady && (
          <div className="absolute inset-0 flex items-center justify-center bg-sky-50/80 text-xs text-slate-400">
            Loading world map...
          </div>
        )}

        {(hoveredNode || hoveredEdge) && (
          <div
            className="absolute z-10 pointer-events-none bg-white border border-sky-200 rounded-lg px-3 py-2 text-xs shadow-lg max-w-xs"
            style={{
              left: Math.min(cursor.x + 12, 720),
              top: Math.max(cursor.y - 10, 0),
            }}
          >
            {hoveredNode && (
              <>
                <div className="font-semibold text-slate-900">
                  {hoveredNode.name}
                </div>
                <div className="text-slate-500">
                  {hoveredNode.category} · {hoveredNode.current_status}
                </div>
                <div className="text-slate-500">
                  Capacity: {hoveredNode.base_capacity.toLocaleString()} units
                </div>
              </>
            )}
            {hoveredEdge && (
              <>
                <div className="font-semibold text-slate-900">
                  {hoveredEdge.source} → {hoveredEdge.target}
                </div>
                <div className="text-slate-500">
                  Mode: {hoveredEdge.mode} · Transit:{" "}
                  {hoveredEdge.transit_days}d
                </div>
                <div className="text-slate-500">
                  Cost: ${hoveredEdge.unit_cost.toLocaleString()} · Risk:{" "}
                  {hoveredEdge.risk_factor.toFixed(2)}x
                </div>
                {hoveredEdge.is_disrupted && (
                  <div className="text-status-critical font-medium mt-0.5">
                    ⚠ Disrupted Route
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {nodes.length > 14 && (
        <p className="text-[11px] text-slate-400 mt-2">
          This network has {nodes.length} nodes — hover any marker to see its name.
        </p>
      )}
    </div>
  );
}

function Legend() {
  const items: { label: string; className: string }[] = [
    { label: "Operational", className: "bg-status-nominal" },
    { label: "Disrupted", className: "bg-status-critical" },
    { label: "AI Reroute", className: "bg-status-reroute" },
  ];
  return (
    <div className="flex items-center gap-3">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          <span
            className={clsx("inline-block w-2.5 h-2.5 rounded-full", item.className)}
          />
          <span className="text-[10px] text-slate-500">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
