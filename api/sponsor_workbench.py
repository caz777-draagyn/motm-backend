"""
API endpoints for sponsor pull workbench.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from utils.sponsor_workbench import (
    GUARANTEED_TYPE_MULTIPLIERS,
    TARGET_LIBRARY,
    OfferGenerationConfig,
    apply_negotiation,
    cancellation_quote,
    compute_offer_count,
    generate_offer_batch,
    generate_slots,
)


router = APIRouter(prefix="/api/sponsor-workbench", tags=["sponsor-workbench"])


class SponsorWorkbenchStorage:
    def __init__(self):
        self.config = OfferGenerationConfig()
        self.week_number = 1
        self.offers: Dict[str, Dict[str, Any]] = {}
        self.contracts: Dict[str, Dict[str, Any]] = {}
        self.slots: List[Dict[str, Any]] = generate_slots(self.config)
        self.history: List[Dict[str, Any]] = []

    def reset(self):
        self.config = OfferGenerationConfig()
        self.week_number = 1
        self.offers = {}
        self.contracts = {}
        self.slots = generate_slots(self.config)
        self.history = []


_storage = SponsorWorkbenchStorage()


class ConfigRequest(BaseModel):
    week_number: int = Field(default=1, ge=1)
    facility_level: int = Field(default=5, ge=0, le=10)
    staff_level: int = Field(default=5, ge=0, le=10)
    min_potential: int = Field(default=1, ge=1, le=20)
    max_potential: int = Field(default=20, ge=1, le=20)
    min_guaranteed_share: float = Field(default=0.25, ge=0.25, le=0.75)
    max_guaranteed_share: float = Field(default=0.75, ge=0.25, le=0.75)
    min_targets_per_offer: int = Field(default=1, ge=1, le=3)
    max_targets_per_offer: int = Field(default=3, ge=1, le=3)
    min_offer_count: int = Field(default=1, ge=1, le=8)
    max_offer_count: int = Field(default=8, ge=1, le=8)
    yearly_base_floor: int = Field(default=60000, ge=1)
    yearly_base_ceiling: int = Field(default=1400000, ge=1)


class PullRequest(BaseModel):
    week_number: Optional[int] = Field(default=None, ge=1)


class NegotiateRequest(BaseModel):
    new_guaranteed_type: str


class AssignSlotRequest(BaseModel):
    slot_id: str


def _serialize_offer(offer: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "offer_id": offer["offer_id"],
        "week_number": offer["week_number"],
        "status": offer["status"],
        "base_potential": offer["base_potential"],
        "duration_years": offer["duration_years"],
        "guaranteed_type": offer["guaranteed_type"],
        "guaranteed_type_label": offer["guaranteed_type_label"],
        "guaranteed_share": offer["guaranteed_share"],
        "yearly_base_value": offer["yearly_base_value"],
        "raw_total_value": offer["raw_total_value"],
        "type_multiplier": offer["type_multiplier"],
        "adjusted_total_value": offer["adjusted_total_value"],
        "guaranteed_value": offer["guaranteed_value"],
        "target_pool_value": offer["target_pool_value"],
        "weekly_guaranteed_payout": offer["weekly_guaranteed_payout"],
        "targets": offer["targets"],
        "negotiated": offer.get("negotiated", False),
        "negotiation_penalty_rate": offer.get("negotiation_penalty_rate", 0.0),
        "diagnostics": offer.get("diagnostics", {}),
    }


def _serialize_contract(contract: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(contract)
    payload["cancellation_quote"] = cancellation_quote(contract, _storage.week_number)
    return payload


@router.post("/reset")
async def reset_state():
    _storage.reset()
    return {"ok": True}


@router.post("/config")
async def set_config(request: ConfigRequest):
    if request.max_potential < request.min_potential:
        raise HTTPException(status_code=400, detail="max_potential must be >= min_potential")
    if request.max_guaranteed_share < request.min_guaranteed_share:
        raise HTTPException(status_code=400, detail="max_guaranteed_share must be >= min_guaranteed_share")
    if request.max_targets_per_offer < request.min_targets_per_offer:
        raise HTTPException(status_code=400, detail="max_targets_per_offer must be >= min_targets_per_offer")
    if request.max_offer_count < request.min_offer_count:
        raise HTTPException(status_code=400, detail="max_offer_count must be >= min_offer_count")
    if request.yearly_base_ceiling < request.yearly_base_floor:
        raise HTTPException(status_code=400, detail="yearly_base_ceiling must be >= yearly_base_floor")

    _storage.config = OfferGenerationConfig(**request.model_dump())
    _storage.week_number = request.week_number
    _storage.slots = generate_slots(_storage.config)
    return {"ok": True, "config": _storage.config.__dict__, "slots": _storage.slots}


@router.post("/pull")
async def pull_weekly_offers(request: PullRequest):
    if request.week_number is not None:
        _storage.week_number = request.week_number
        _storage.config.week_number = request.week_number

    offer_count = compute_offer_count(_storage.config)
    generated = generate_offer_batch(_storage.config, offer_count)

    _storage.offers = {}
    for offer in generated:
        offer_id = str(uuid4())
        offer_record = {
            "offer_id": offer_id,
            "week_number": _storage.week_number,
            "status": "offered",
            "created_at": datetime.utcnow().isoformat(),
            **offer,
        }
        _storage.offers[offer_id] = offer_record

    return {
        "week_number": _storage.week_number,
        "offer_count": offer_count,
        "offers": [_serialize_offer(offer) for offer in _storage.offers.values()],
    }


@router.post("/offers/{offer_id}/negotiate")
async def negotiate_offer(offer_id: str, request: NegotiateRequest):
    offer = _storage.offers.get(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer["status"] != "offered":
        raise HTTPException(status_code=400, detail="Only offered deals can be negotiated")
    if offer.get("negotiated", False):
        raise HTTPException(status_code=400, detail="Offer already negotiated")
    if request.new_guaranteed_type not in GUARANTEED_TYPE_MULTIPLIERS:
        raise HTTPException(status_code=400, detail="Invalid guaranteed type")

    updated, meta = apply_negotiation(offer, request.new_guaranteed_type)
    _storage.offers[offer_id] = updated
    return {"offer": _serialize_offer(updated), "negotiation_meta": meta}


@router.post("/offers/{offer_id}/accept")
async def accept_offer(offer_id: str):
    offer = _storage.offers.get(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer["status"] != "offered":
        raise HTTPException(status_code=400, detail="Offer cannot be accepted")

    contract_id = str(uuid4())
    contract = {
        "contract_id": contract_id,
        "source_offer_id": offer_id,
        "status": "accepted_unassigned",
        "start_week": _storage.week_number,
        "duration_years": offer["duration_years"],
        "guaranteed_type": offer["guaranteed_type"],
        "guaranteed_type_label": offer["guaranteed_type_label"],
        "guaranteed_value": offer["guaranteed_value"],
        "weekly_guaranteed_payout": offer["weekly_guaranteed_payout"],
        "target_pool_value": offer["target_pool_value"],
        "targets": offer["targets"],
        "adjusted_total_value": offer["adjusted_total_value"],
        "slot_id": None,
        "cancelled_at_week": None,
    }
    _storage.contracts[contract_id] = contract
    offer["status"] = "accepted"
    _storage.history.append({"event": "accepted", "offer_id": offer_id, "contract_id": contract_id, "week": _storage.week_number})

    return {"contract": _serialize_contract(contract)}


@router.post("/contracts/{contract_id}/assign-slot")
async def assign_slot(contract_id: str, request: AssignSlotRequest):
    contract = _storage.contracts.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Cancelled contracts cannot be slotted")
    if contract.get("slot_id"):
        raise HTTPException(status_code=400, detail="Contract is already assigned to a slot")

    slot = next((s for s in _storage.slots if s["slot_id"] == request.slot_id), None)
    if slot is None:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot["occupied_contract_id"]:
        raise HTTPException(status_code=400, detail="Slot already occupied")

    slot["occupied_contract_id"] = contract_id
    contract["slot_id"] = slot["slot_id"]
    contract["status"] = "active_slotted"
    _storage.history.append({"event": "slotted", "contract_id": contract_id, "slot_id": slot["slot_id"], "week": _storage.week_number})
    return {"contract": _serialize_contract(contract), "slot": slot}


@router.post("/contracts/{contract_id}/cancel")
async def cancel_contract(contract_id: str):
    contract = _storage.contracts.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Contract already cancelled")

    quote = cancellation_quote(contract, _storage.week_number)
    if not quote["cancellable"]:
        raise HTTPException(status_code=400, detail=quote["reason"])

    slot_id = contract.get("slot_id")
    if slot_id:
        slot = next((s for s in _storage.slots if s["slot_id"] == slot_id), None)
        if slot:
            slot["occupied_contract_id"] = None

    contract["status"] = "cancelled"
    contract["cancelled_at_week"] = _storage.week_number
    _storage.history.append(
        {"event": "cancelled", "contract_id": contract_id, "week": _storage.week_number, "cancel_fee": quote["cancel_fee"]}
    )
    return {"contract": _serialize_contract(contract), "cancel_fee": quote["cancel_fee"], "reason": quote["reason"]}


@router.get("/state")
async def get_state():
    return {
        "week_number": _storage.week_number,
        "config": _storage.config.__dict__,
        "offers": [_serialize_offer(offer) for offer in _storage.offers.values()],
        "contracts": [_serialize_contract(contract) for contract in _storage.contracts.values()],
        "slots": _storage.slots,
        "history": _storage.history,
        "constants": {
            "guaranteed_type_multipliers": GUARANTEED_TYPE_MULTIPLIERS,
            "target_library": TARGET_LIBRARY,
        },
    }


@router.get("/", response_class=HTMLResponse)
async def sponsor_workbench_ui():
    try:
        with open("templates/sponsor_workbench.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Sponsor Workbench UI not found</h1><p>Please create templates/sponsor_workbench.html</p>",
            status_code=404,
        )
