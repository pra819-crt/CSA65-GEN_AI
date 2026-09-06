"""
API v1 route definitions.

All HTTP + WebSocket endpoints for the Supply Chain Digital Twin system
live here and are mounted under `/api/v1` by app/main.py. Every route
requires an authenticated user (Bearer JWT); `/reset` additionally
requires the `admin` role.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.deps import get_current_admin, get_current_user
from app.core.security import decode_access_token
from app.models.schemas import (
    GenerateChainRequest,
    GenerateChainResponse,
    NetworkResponse,
    OptimizeRequest,
    OptimizeResponse,
    ResetResponse,
    SimulateRequest,
    SimulateResponse,
    StreamUpdate,
    SuggestScenariosResponse,
    UserOut,
)
from app.services.ai_simulator import get_ai_simulator
from app.services.optimizer import compute_route_comparison
from app.services.twin_engine import get_twin
from app.services.user_store import get_user_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/network", response_model=NetworkResponse, summary="Get current network state")
async def get_network(current_user: UserOut = Depends(get_current_user)) -> NetworkResponse:
    twin = get_twin()
    return twin.get_network_json()


@router.post("/simulate", response_model=SimulateResponse, summary="Run AI disruption simulation")
async def simulate_disruption(
    request: SimulateRequest, current_user: UserOut = Depends(get_current_user)
) -> SimulateResponse:
    twin = get_twin()
    simulator = get_ai_simulator()

    current_network = twin.get_network_json()

    try:
        analysis = await simulator.analyze_disruption(request.prompt, current_network)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during AI disruption analysis")
        raise HTTPException(status_code=500, detail="AI simulation failed") from exc

    twin.apply_disruption(
        node_ids=analysis.impacted_node_ids,
        edge_ids=analysis.impacted_edge_ids,
        delay_mult=analysis.delay_multiplier,
        cost_mult=analysis.cost_multiplier,
    )

    return SimulateResponse(analysis=analysis, network=twin.get_network_json())


@router.post(
    "/twin/generate-chain",
    response_model=GenerateChainResponse,
    summary="Generate a supply chain network from the user's own description",
)
async def generate_chain(
    request: GenerateChainRequest, current_user: UserOut = Depends(get_current_user)
) -> GenerateChainResponse:
    twin = get_twin()
    simulator = get_ai_simulator()

    try:
        network, summary = await simulator.generate_chain(request.description)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during chain generation")
        raise HTTPException(status_code=500, detail="Chain generation failed") from exc

    twin.load_custom_network(network.nodes, network.edges)
    return GenerateChainResponse(network=twin.get_network_json(), summary=summary)


@router.post(
    "/twin/restore-default",
    response_model=NetworkResponse,
    summary="Discard the user's custom chain and restore the built-in demo network",
)
async def restore_default_network(
    current_user: UserOut = Depends(get_current_user),
) -> NetworkResponse:
    twin = get_twin()
    twin.restore_default_demo_network()
    return twin.get_network_json()


@router.get(
    "/twin/suggest-scenarios",
    response_model=SuggestScenariosResponse,
    summary="AI-suggested disruption scenarios tailored to the current network",
)
async def suggest_scenarios(
    current_user: UserOut = Depends(get_current_user),
) -> SuggestScenariosResponse:
    twin = get_twin()
    simulator = get_ai_simulator()
    network = twin.get_network_json()

    try:
        scenarios = await simulator.suggest_scenarios(network)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during scenario suggestion")
        raise HTTPException(status_code=500, detail="Scenario suggestion failed") from exc

    return SuggestScenariosResponse(scenarios=scenarios)


@router.post("/optimize", response_model=OptimizeResponse, summary="Compute optimal reroute")
async def optimize_route(
    request: OptimizeRequest, current_user: UserOut = Depends(get_current_user)
) -> OptimizeResponse:
    twin = get_twin()

    if twin.get_node(request.source_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown source_id: {request.source_id}")
    if twin.get_node(request.target_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown target_id: {request.target_id}")

    (
        baseline,
        disrupted,
        optimized,
        ttr_days,
        cost_overhead_pct,
        time_saved_days,
    ) = compute_route_comparison(
        twin,
        request.source_id,
        request.target_id,
        request.delay_multiplier,
        request.cost_multiplier,
    )

    return OptimizeResponse(
        baseline=baseline,
        disrupted=disrupted,
        optimized=optimized,
        time_to_recovery_days=ttr_days,
        cost_overhead_pct=cost_overhead_pct,
        time_saved_days=time_saved_days,
    )


@router.post(
    "/reset",
    response_model=ResetResponse,
    summary="Reset network to baseline (admin only)",
)
async def reset_network(current_admin: UserOut = Depends(get_current_admin)) -> ResetResponse:
    twin = get_twin()
    twin.reset_network()
    return ResetResponse()


@router.websocket("/stream-sim")
async def stream_simulation(websocket: WebSocket) -> None:
    """
    Real-time scenario streaming.

    Client must send an initial auth message before anything else:
        {"token": "<JWT access token>"}
    followed by scenario messages:
        {"prompt": "..."}

    Server streams sequential StreamUpdate JSON messages representing
    progress steps, finishing with the full SimulateResponse payload.
    """
    await websocket.accept()
    twin = get_twin()
    simulator = get_ai_simulator()
    store = get_user_store()

    # --- Handshake: require a valid token before accepting any prompts ---
    try:
        auth_msg = await websocket.receive_json()
        token = auth_msg.get("token", "")
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username or store.get_user_out(username) is None:
            raise JWTError("Unknown user")
    except Exception:  # noqa: BLE001
        await websocket.send_json(
            StreamUpdate(step="error", progress=100, message="Authentication failed.").model_dump()
        )
        await websocket.close(code=4401)
        return

    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt", "").strip()

            if not prompt or len(prompt) < 5:
                await websocket.send_json(
                    StreamUpdate(
                        step="error", progress=100, message="Prompt too short."
                    ).model_dump()
                )
                continue

            steps = [
                ("ingest", 10, "Ingesting disruption prompt..."),
                ("network_snapshot", 25, "Snapshotting current Digital Twin state..."),
                ("ai_analysis", 55, "Querying Gemini for disruption impact analysis..."),
            ]
            for step, progress, message in steps:
                await websocket.send_json(
                    StreamUpdate(step=step, progress=progress, message=message).model_dump()
                )
                await asyncio.sleep(0.3)

            current_network = twin.get_network_json()
            try:
                analysis = await simulator.analyze_disruption(prompt, current_network)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Streaming simulation failed")
                await websocket.send_json(
                    StreamUpdate(
                        step="error", progress=100, message=f"Simulation failed: {exc}"
                    ).model_dump()
                )
                continue

            await websocket.send_json(
                StreamUpdate(
                    step="applying_disruption", progress=80,
                    message="Applying disruption weights to Digital Twin...",
                ).model_dump()
            )

            twin.apply_disruption(
                node_ids=analysis.impacted_node_ids,
                edge_ids=analysis.impacted_edge_ids,
                delay_mult=analysis.delay_multiplier,
                cost_mult=analysis.cost_multiplier,
            )

            result = SimulateResponse(analysis=analysis, network=twin.get_network_json())
            await websocket.send_json(
                StreamUpdate(
                    step="complete", progress=100, message="Simulation complete.",
                    payload=result.model_dump(),
                ).model_dump()
            )

    except WebSocketDisconnect:
        logger.info("Client disconnected from stream-sim WebSocket")
