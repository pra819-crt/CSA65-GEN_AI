import axios, { AxiosError, AxiosInstance } from "axios";
import {
  AuthToken,
  GenerateChainResponse,
  NetworkResponse,
  OptimizeResponse,
  ResetResponse,
  SimulateResponse,
  SuggestScenariosResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const client: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// The access token lives only in memory for the lifetime of the tab.
// It is intentionally NOT persisted to localStorage/cookies, so that
// reopening the app always requires signing in again.
let currentToken: string | null = null;

export function setAuthToken(token: string | null): void {
  currentToken = token;
  if (token) {
    client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete client.defaults.headers.common["Authorization"];
  }
}

export function getAuthToken(): string | null {
  return currentToken;
}

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function unwrapError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail?: string }>;
    const detail = axiosErr.response?.data?.detail;
    return new ApiError(
      detail || axiosErr.message || "Unknown API error",
      axiosErr.response?.status
    );
  }
  return new ApiError(
    error instanceof Error ? error.message : "Unknown error occurred"
  );
}

// --- Auth ---

export async function registerUser(
  username: string,
  password: string,
  fullName?: string
): Promise<AuthToken> {
  try {
    const { data } = await client.post<AuthToken>("/auth/register", {
      username,
      password,
      full_name: fullName || undefined,
    });
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

export async function loginUser(
  username: string,
  password: string
): Promise<AuthToken> {
  try {
    const { data } = await client.post<AuthToken>("/auth/login", {
      username,
      password,
    });
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

// --- Digital Twin ---

export async function fetchNetwork(): Promise<NetworkResponse> {
  try {
    const { data } = await client.get<NetworkResponse>("/network");
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

export async function simulateDisruption(
  prompt: string
): Promise<SimulateResponse> {
  try {
    const { data } = await client.post<SimulateResponse>("/simulate", {
      prompt,
    });
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

export async function optimizeRoute(
  sourceId: string,
  targetId: string,
  delayMultiplier: number = 1.0,
  costMultiplier: number = 1.0
): Promise<OptimizeResponse> {
  try {
    const { data } = await client.post<OptimizeResponse>("/optimize", {
      source_id: sourceId,
      target_id: targetId,
      delay_multiplier: delayMultiplier,
      cost_multiplier: costMultiplier,
    });
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

export async function resetNetwork(): Promise<ResetResponse> {
  try {
    const { data } = await client.post<ResetResponse>("/reset");
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

export async function generateChain(
  description: string
): Promise<GenerateChainResponse> {
  try {
    const { data } = await client.post<GenerateChainResponse>(
      "/twin/generate-chain",
      { description }
    );
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

export async function restoreDefaultNetwork(): Promise<NetworkResponse> {
  try {
    const { data } = await client.post<NetworkResponse>("/twin/restore-default");
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

export async function suggestScenarios(): Promise<SuggestScenariosResponse> {
  try {
    const { data } = await client.get<SuggestScenariosResponse>(
      "/twin/suggest-scenarios"
    );
    return data;
  } catch (err) {
    throw unwrapError(err);
  }
}

/**
 * Opens an authenticated WebSocket connection to /stream-sim. The caller
 * must send {"token": "<access token>"} as the first message before any
 * prompts, matching the backend's handshake.
 */
export function openSimulationStream(): WebSocket {
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  return new WebSocket(`${wsBase}/stream-sim`);
}
