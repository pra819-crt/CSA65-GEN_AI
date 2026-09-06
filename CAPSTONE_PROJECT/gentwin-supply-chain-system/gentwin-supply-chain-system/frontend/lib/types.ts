export type NodeCategory =
  | "Supplier"
  | "Factory"
  | "Port"
  | "Warehouse"
  | "Retailer"
  | "Hub";

export type TransportMode = "Sea" | "Air" | "Road" | "Rail";

export type NodeStatus = "Operational" | "Disrupted" | "Degraded";

export type UserRole = "user" | "admin";

export interface TwinNode {
  id: string;
  name: string;
  category: NodeCategory;
  lat: number;
  lng: number;
  base_capacity: number;
  current_status: NodeStatus;
}

export interface TwinEdge {
  id: string;
  source: string;
  target: string;
  mode: TransportMode;
  transit_days: number;
  unit_cost: number;
  risk_factor: number;
  is_disrupted: boolean;
}

export interface NetworkResponse {
  nodes: TwinNode[];
  edges: TwinEdge[];
}

export interface DisruptionAnalysis {
  scenario_title: string;
  executive_summary: string;
  impacted_node_ids: string[];
  impacted_edge_ids: string[];
  delay_multiplier: number;
  cost_multiplier: number;
  overall_severity_score: number;
  risk_mitigation_recommendations: string[];
}

export interface SimulateResponse {
  analysis: DisruptionAnalysis;
  network: NetworkResponse;
}

export interface RouteResult {
  path: string[];
  edge_ids: string[];
  total_cost: number;
  total_transit_days: number;
  total_weight: number;
  feasible: boolean;
}

export interface OptimizeResponse {
  baseline: RouteResult;
  disrupted: RouteResult;
  optimized: RouteResult;
  time_to_recovery_days: number;
  cost_overhead_pct: number;
  time_saved_days: number;
}

export interface ResetResponse {
  status: string;
  message: string;
}

export interface StreamUpdate {
  step: string;
  progress: number;
  message: string;
  payload?: SimulateResponse | null;
}

// --- Auth ---

export interface AuthUser {
  username: string;
  full_name?: string | null;
  role: UserRole;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: AuthUser;
}

// --- User-defined chains + AI-suggested scenarios ---

export interface GenerateChainResponse {
  network: NetworkResponse;
  summary: string;
}

export interface ScenarioSuggestion {
  title: string;
  prompt: string;
  risk_level: "Low" | "Medium" | "High";
}

export interface SuggestScenariosResponse {
  scenarios: ScenarioSuggestion[];
}
