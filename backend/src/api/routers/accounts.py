"""
Accounts Configuration Router — T018 (schemas), T019 (CRUD), T023 (data migration)
Handles GET/PUT of per-account visibility & data-separation settings,
including Shared→Separated and Separated→Shared data transitions.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from src.api.dependencies import get_active_account
from src.core.database import db_holder

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/accounts", tags=["accounts"])

# ── Constants ────────────────────────────────────────────────────────────────

ALL_ITEMS = [
    "series", "animes", "youtube", "light_novels",
    "manga", "jogos", "financas", "saude_fitness",
    "links", "trabalho", "estudos", "filmes",
]

VALID_ACCOUNTS = {"car-j-works", "car-j-home"}


# ── Pydantic Schemas (T018) ──────────────────────────────────────────────────

class ItemSettingsMap(BaseModel):
    """Map of item_id → boolean for visibility or separation settings."""
    series: bool = True
    animes: bool = True
    youtube: bool = True
    light_novels: bool = True
    manga: bool = True
    jogos: bool = True
    financas: bool = True
    saude_fitness: bool = True
    links: bool = True
    trabalho: bool = True
    estudos: bool = True
    filmes: bool = True

    def to_dict(self) -> dict:
        return self.model_dump()


class TransitionOption(BaseModel):
    """Specifies how to handle data when a utility changes sharing mode."""
    action: str  # "separate" | "merge"
    inherit_account_id: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ("separate", "merge"):
            raise ValueError("action must be 'separate' or 'merge'")
        return v

    @field_validator("inherit_account_id")
    @classmethod
    def validate_inherit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_ACCOUNTS:
            raise ValueError(f"inherit_account_id must be one of {VALID_ACCOUNTS}")
        return v


class AccountConfigUpdate(BaseModel):
    """PUT request body for updating account configuration."""
    account_id: str
    visibility_settings: ItemSettingsMap
    data_separation_settings: ItemSettingsMap
    transition_options: Optional[dict[str, TransitionOption]] = None

    @field_validator("account_id")
    @classmethod
    def validate_account(cls, v: str) -> str:
        if v not in VALID_ACCOUNTS:
            raise ValueError(f"account_id must be one of {VALID_ACCOUNTS}")
        return v


class AccountConfigResponse(BaseModel):
    """Single account configuration payload."""
    account_id: str
    visibility_settings: dict
    data_separation_settings: dict


# ── CRUD helpers (T019) ──────────────────────────────────────────────────────

async def _get_config(account_id: str) -> dict:
    col = db_holder.db["accounts_config"]
    doc = await col.find_one({"_id": account_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found")
    return doc


async def _update_config(account_id: str, visibility: dict, separation: dict) -> None:
    col = db_holder.db["accounts_config"]
    await col.update_one(
        {"_id": account_id},
        {"$set": {
            "visibility_settings": visibility,
            "data_separation_settings": separation,
        }},
        upsert=True,
    )


# ── Data migration helpers (T023) ────────────────────────────────────────────

async def _migrate_shared_to_separated(item_type: str, inherit_account_id: str) -> None:
    """
    Shared → Separated: Tag all existing records with inherit_account_id.
    The other account starts with an empty slate.
    """
    col = db_holder.db[item_type]
    result = await col.update_many(
        {"account_id": {"$in": [None, ""]}},
        {"$set": {"account_id": inherit_account_id}},
    )
    logger.info(
        "Separated '%s': %d records tagged to '%s'",
        item_type, result.modified_count, inherit_account_id,
    )


async def _migrate_separated_to_shared(item_type: str) -> None:
    """
    Separated → Shared: Remove account_id tag from all records so both
    accounts see everything.
    """
    col = db_holder.db[item_type]
    result = await col.update_many(
        {"account_id": {"$exists": True}},
        {"$unset": {"account_id": ""}},
    )
    logger.info(
        "Merged '%s': %d records untagged (now shared)",
        item_type, result.modified_count,
    )


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/config", response_model=dict[str, AccountConfigResponse])
async def get_all_configs(_: str = Depends(get_active_account)):
    """Return visibility & separation settings for both accounts."""
    results: dict[str, AccountConfigResponse] = {}
    for account_id in VALID_ACCOUNTS:
        try:
            doc = await _get_config(account_id)
        except HTTPException:
            continue
        results[account_id] = AccountConfigResponse(
            account_id=account_id,
            visibility_settings=doc.get("visibility_settings", {}),
            data_separation_settings=doc.get("data_separation_settings", {}),
        )
    return results


@router.put("/config")
async def update_config(
    body: AccountConfigUpdate,
    _: str = Depends(get_active_account),
):
    """
    Update account config. If transition_options provided, migrate data
    for affected item types before persisting the new settings.
    """
    # Fetch current separation state to detect changes
    try:
        current = await _get_config(body.account_id)
    except HTTPException:
        current = {}

    current_sep: dict = current.get("data_separation_settings", {})
    new_sep: dict = body.data_separation_settings.to_dict()

    # Run migrations for items whose sharing mode changed
    if body.transition_options:
        for item_type, transition in body.transition_options.items():
            was_separated = current_sep.get(item_type, False)
            will_be_separated = new_sep.get(item_type, False)

            if not was_separated and will_be_separated:
                # Shared → Separated
                if transition.action != "separate":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Expected action='separate' for item '{item_type}'",
                    )
                if not transition.inherit_account_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"'inherit_account_id' required when separating '{item_type}'",
                    )
                await _migrate_shared_to_separated(item_type, transition.inherit_account_id)

            elif was_separated and not will_be_separated:
                # Separated → Shared
                if transition.action != "merge":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Expected action='merge' for item '{item_type}'",
                    )
                await _migrate_separated_to_shared(item_type)

    # Persist updated settings
    await _update_config(
        body.account_id,
        body.visibility_settings.to_dict(),
        new_sep,
    )

    return {"status": "success", "message": "Account configuration updated successfully."}
