"""
Pydantic v2 schemas for the Supply Chain Digital Twin system.

These models are used for:
  - Graph node / edge serialization
  - API request / response contracts
  - Gemini structured-output parsing (DisruptionAnalysis)
  - Authentication (user registration, login, tokens)
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class NodeCategory(str, Enum):
    SUPPLIER = "Supplier"
    FACTORY = "Factory"
    PORT = "Port"
    WAREHOUSE = "Warehouse"
    RETAILER = "Retailer"
    HUB = "Hub"


class TransportMode(str, Enum):
    SEA = "Sea"
    AIR = "Air"
    ROAD = "Road"
    RAIL = "Rail"


class NodeStatus(str, Enum):
    OPERATIONAL = "Operational"
    DISRUPTED = "Disrupted"
    DEGRADED = "Degraded"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


# --------------------------------------------------------------------------
# Graph primitives
# --------------------------------------------------------------------------

class Node(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    name: str
    category: NodeCategory
    lat: float
    lng: float
    base_capacity: int = Field(gt=0)
    current_status: NodeStatus = NodeStatus.OPERATIONAL


class Edge(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    source: str
    target: str
    mode: TransportMode
    transit_days: float = Field(gt=0)
    unit_cost: float = Field(gt=0)
    risk_factor: float = Field(default=1.0, ge=0.1)
    is_disrupted: bool = False


class NetworkResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


# --------------------------------------------------------------------------
# Gemini structured output contract
# --------------------------------------------------------------------------

class DisruptionAnalysis(BaseModel):
    """Structured output schema enforced on the Gemini response."""

    scenario_title: str
    executive_summary: str
    impacted_node_ids: List[str] = Field(default_factory=list)
    impacted_edge_ids: List[str] = Field(default_factory=list)
    delay_multiplier: float = Field(ge=1.0, description="e.g. 1.5 = +50% delay")
    cost_multiplier: float = Field(ge=1.0, description="e.g. 2.1 = +110% cost increase")
    overall_severity_score: int = Field(ge=0, le=100)
    risk_mitigation_recommendations: List[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Core API request / response payloads
# --------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=2000)


class SimulateResponse(BaseModel):
    analysis: DisruptionAnalysis
    network: NetworkResponse


class OptimizeRequest(BaseModel):
    source_id: str
    target_id: str
    delay_multiplier: float = Field(default=1.0, ge=1.0)
    cost_multiplier: float = Field(default=1.0, ge=1.0)


class RouteResult(BaseModel):
    path: List[str]
    edge_ids: List[str]
    total_cost: float
    total_transit_days: float
    total_weight: float
    feasible: bool = True


class OptimizeResponse(BaseModel):
    baseline: RouteResult
    disrupted: RouteResult
    optimized: RouteResult
    time_to_recovery_days: float
    cost_overhead_pct: float
    time_saved_days: float


class ResetResponse(BaseModel):
    status: str = "reset"
    message: str = "Network state has been reset to baseline."


class StreamUpdate(BaseModel):
    """Message envelope pushed over the /stream-sim WebSocket."""

    step: str
    progress: int = Field(ge=0, le=100)
    message: str
    payload: Optional[dict] = None


# --------------------------------------------------------------------------
# User-supplied chain generation + AI-suggested disruption scenarios
# --------------------------------------------------------------------------

class GenerateChainRequest(BaseModel):
    description: str = Field(
        min_length=10,
        max_length=3000,
        description=(
            "Plain-language description of the person's own supply chain, "
            "e.g. supplier and factory locations, warehouses, key routes."
        ),
    )


class GenerateChainResponse(BaseModel):
    network: NetworkResponse
    summary: str = Field(description="Short plain-language recap of the generated chain.")


class ScenarioSuggestion(BaseModel):
    title: str
    prompt: str = Field(description="Full disruption prompt, ready to pass to /simulate.")
    risk_level: str = Field(description="Low, Medium, or High")


class SuggestScenariosResponse(BaseModel):
    scenarios: List[ScenarioSuggestion]


# --------------------------------------------------------------------------
# Auth request / response payloads
# --------------------------------------------------------------------------

USERNAME_PATTERN = r"^[a-zA-Z0-9_]{3,32}$"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=USERNAME_PATTERN)
    password: str = Field(min_length=6, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("Password cannot be blank")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str
    full_name: Optional[str] = None
    role: UserRole
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserOut
