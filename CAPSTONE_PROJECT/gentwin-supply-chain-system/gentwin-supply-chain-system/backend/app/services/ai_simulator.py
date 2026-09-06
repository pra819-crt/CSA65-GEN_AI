"""
Generative AI Disruption Engine.

Uses the google-genai SDK to turn a natural-language disruption prompt
(e.g. "Suez canal blocked for 12 days") into a structured
DisruptionAnalysis object, constrained to valid node/edge IDs from the
live Digital Twin so the result can be applied directly to the graph.
"""

from __future__ import annotations

import json
import logging
from typing import List

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.core.config import get_settings
from app.models.schemas import (
    DisruptionAnalysis,
    Edge,
    NetworkResponse,
    Node,
    ScenarioSuggestion,
)

logger = logging.getLogger(__name__)

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "scenario_title": {"type": "string"},
        "executive_summary": {"type": "string"},
        "impacted_node_ids": {"type": "array", "items": {"type": "string"}},
        "impacted_edge_ids": {"type": "array", "items": {"type": "string"}},
        "delay_multiplier": {"type": "number"},
        "cost_multiplier": {"type": "number"},
        "overall_severity_score": {"type": "integer"},
        "risk_mitigation_recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "scenario_title",
        "executive_summary",
        "impacted_node_ids",
        "impacted_edge_ids",
        "delay_multiplier",
        "cost_multiplier",
        "overall_severity_score",
        "risk_mitigation_recommendations",
    ],
}


_CHAIN_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["Supplier", "Factory", "Port", "Warehouse", "Retailer", "Hub"],
                    },
                    "lat": {"type": "number"},
                    "lng": {"type": "number"},
                    "base_capacity": {"type": "integer"},
                },
                "required": ["id", "name", "category", "lat", "lng", "base_capacity"],
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "mode": {"type": "string", "enum": ["Sea", "Air", "Road", "Rail"]},
                    "transit_days": {"type": "number"},
                    "unit_cost": {"type": "number"},
                },
                "required": ["id", "source", "target", "mode", "transit_days", "unit_cost"],
            },
        },
    },
    "required": ["summary", "nodes", "edges"],
}

_SCENARIOS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "scenarios": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "prompt": {"type": "string"},
                    "risk_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
                },
                "required": ["title", "prompt", "risk_level"],
            },
        },
    },
    "required": ["scenarios"],
}


def _friendly_gemini_error(exc: "genai_errors.APIError") -> str:
    """Turn a raw google-genai APIError into an actionable, non-technical message."""
    code = getattr(exc, "code", None)
    message = str(exc)

    if code == 429 or "RESOURCE_EXHAUSTED" in message:
        return (
            "The Gemini API quota for this key has been used up "
            "(Google's free tier caps this at a small number of requests per day). "
            "Wait for the quota to reset, or add billing / upgrade your plan at "
            "https://ai.google.dev/gemini-api/docs/rate-limits."
        )
    if code == 401 or code == 403:
        return (
            "The Gemini API rejected this request as unauthorized. "
            "Double-check that GEMINI_API_KEY in your .env file is correct and active."
        )
    if code and code >= 500:
        return "The Gemini API is temporarily unavailable. Please try again shortly."
    return f"The Gemini API returned an error (HTTP {code}): {message}"


class AIDisruptionSimulator:
    """Thin wrapper around google-genai for structured disruption analysis."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not self._settings.GEMINI_API_KEY:
                raise RuntimeError(
                    "GEMINI_API_KEY is not configured. Set it in your .env file."
                )
            self._client = genai.Client(api_key=self._settings.GEMINI_API_KEY)
        return self._client

    async def _generate(
        self, prompt: str, response_schema: dict, temperature: float
    ) -> str:
        """
        Call Gemini with structured-output enforcement, normalizing any
        API-level failure (auth, rate limit, quota, server error) into a
        RuntimeError with a clear, user-facing message. The router layer
        maps RuntimeError to HTTP 503, so callers always get an
        understandable error instead of a raw stack trace.
        """
        client = self._get_client()
        try:
            response = await client.aio.models.generate_content(
                model=self._settings.GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=temperature,
                ),
            )
            return response.text
        except genai_errors.APIError as exc:
            raise RuntimeError(_friendly_gemini_error(exc)) from exc
        except Exception as exc:  # noqa: BLE001 — network/timeout/etc.
            raise RuntimeError(
                f"Could not reach the Gemini API: {exc}"
            ) from exc

    @staticmethod
    def _build_prompt(user_prompt: str, network: NetworkResponse) -> str:
        node_ids = [n.id for n in network.nodes]
        edge_ids = [e.id for e in network.edges]
        node_lines = "\n".join(
            f"- {n.id}: {n.name} ({n.category})" for n in network.nodes
        )
        edge_lines = "\n".join(
            f"- {e.id}: {e.source} -> {e.target} via {e.mode} "
            f"(transit_days={e.transit_days}, unit_cost={e.unit_cost})"
            for e in network.edges
        )
        return f"""You are a supply chain risk analyst embedded in a Digital Twin
simulation platform. Analyze the following disruption scenario and produce
a structured impact assessment.

VALID NODE IDS (only use these in impacted_node_ids): {node_ids}
VALID EDGE IDS (only use these in impacted_edge_ids): {edge_ids}

NETWORK NODES:
{node_lines}

NETWORK EDGES:
{edge_lines}

DISRUPTION SCENARIO PROMPT:
\"\"\"{user_prompt}\"\"\"

Instructions:
1. Identify which of the listed nodes and edges would realistically be impacted
   by this scenario. Only reference IDs from the valid lists above.
2. Estimate delay_multiplier (>= 1.0, e.g. 1.5 means +50% transit delay) and
   cost_multiplier (>= 1.0, e.g. 2.1 means +110% cost increase) for the
   impacted routes.
3. Assign overall_severity_score from 0 (negligible) to 100 (catastrophic).
4. Provide 3-5 concrete, actionable risk_mitigation_recommendations.
5. Write a concise executive_summary (2-4 sentences) and a short scenario_title.
"""

    async def analyze_disruption(
        self, user_prompt: str, network: NetworkResponse
    ) -> DisruptionAnalysis:
        """Call Gemini with structured output enforcement and parse the result."""
        prompt = self._build_prompt(user_prompt, network)
        raw_text = await self._generate(prompt, _RESPONSE_SCHEMA, temperature=0.4)

        try:
            parsed = json.loads(raw_text)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("Failed to parse Gemini structured output: %s", raw_text)
            raise ValueError("Gemini returned malformed structured output") from exc

        valid_node_ids = {n.id for n in network.nodes}
        valid_edge_ids = {e.id for e in network.edges}
        parsed["impacted_node_ids"] = [
            nid for nid in parsed.get("impacted_node_ids", []) if nid in valid_node_ids
        ]
        parsed["impacted_edge_ids"] = [
            eid for eid in parsed.get("impacted_edge_ids", []) if eid in valid_edge_ids
        ]

        return DisruptionAnalysis(**parsed)

    async def generate_chain(self, description: str) -> tuple[NetworkResponse, str]:
        """
        Turn a person's own plain-language description of their supply chain
        into a NetworkResponse (nodes + edges) they can simulate against.
        """
        prompt = f"""You are a supply chain data modeler. A user has described their
own supply chain in plain language. Convert it into a structured network graph.

USER'S DESCRIPTION:
\"\"\"{description}\"\"\"

Instructions:
1. Create 4-10 nodes representing the suppliers, factories, ports, warehouses,
   retailers, or hubs mentioned or reasonably implied by the description.
2. Give each node a short unique snake_case id (e.g. "factory_pune"), a
   human-readable name, a category, an approximate real-world latitude and
   longitude for its location, and a reasonable base_capacity (units/month).
3. Create edges connecting the nodes into a sensible, connected network
   (every node should be reachable). Pick a realistic transport mode,
   transit_days, and unit_cost for each edge based on distance and mode.
4. Every edge's source and target MUST exactly match a node id you created.
5. Write a 2-3 sentence summary of the chain you built.
Keep the network compact and realistic; do not invent unrelated locations."""

        raw_text = await self._generate(prompt, _CHAIN_RESPONSE_SCHEMA, temperature=0.5)

        try:
            parsed = json.loads(raw_text)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("Failed to parse Gemini chain-generation output: %s", raw_text)
            raise ValueError("Gemini returned malformed chain data") from exc

        nodes = [Node(**n) for n in parsed["nodes"]]
        node_ids = {n.id for n in nodes}
        edges = [Edge(**e) for e in parsed["edges"] if e["source"] in node_ids and e["target"] in node_ids]

        if not nodes or not edges:
            raise ValueError("Gemini did not return a usable network (missing nodes or edges).")

        return NetworkResponse(nodes=nodes, edges=edges), parsed["summary"]

    async def suggest_scenarios(self, network: NetworkResponse) -> List[ScenarioSuggestion]:
        """Given the current twin network, suggest 3-4 realistic disruption scenarios."""
        node_lines = "\n".join(f"- {n.id}: {n.name} ({n.category})" for n in network.nodes)
        edge_lines = "\n".join(
            f"- {e.source} -> {e.target} via {e.mode}" for e in network.edges
        )
        prompt = f"""You are a supply chain risk analyst. Given this network, suggest
3 to 4 realistic, varied disruption scenarios a user could simulate.

NODES:
{node_lines}

ROUTES:
{edge_lines}

For each scenario, give a short title, a 1-2 sentence natural-language prompt
suitable for feeding directly into a disruption simulator, and a risk_level
(Low, Medium, or High). Vary the type of disruption (e.g. weather, labor,
geopolitical, factory outage, port congestion) and make each one specific
to the nodes/routes above, not generic."""

        raw_text = await self._generate(prompt, _SCENARIOS_RESPONSE_SCHEMA, temperature=0.7)

        try:
            parsed = json.loads(raw_text)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("Failed to parse Gemini scenario suggestions: %s", raw_text)
            raise ValueError("Gemini returned malformed scenario data") from exc

        return [ScenarioSuggestion(**s) for s in parsed["scenarios"]]


_simulator_instance: AIDisruptionSimulator | None = None


def get_ai_simulator() -> AIDisruptionSimulator:
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = AIDisruptionSimulator()
    return _simulator_instance
