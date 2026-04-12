"""
Supabase client helpers for data-service persistence.
"""

from __future__ import annotations

import os
from functools import lru_cache

from postgrest.exceptions import APIError
from supabase import Client, create_client

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TRANSACTIONS_TABLE = os.getenv("SUPABASE_TRANSACTIONS_TABLE", "transactions")


def _missing_configuration_message() -> str:
    return (
        "Supabase is not configured for data-service. "
        "Set SUPABASE_URL (or VITE_SUPABASE_URL) and SUPABASE_SERVICE_ROLE_KEY in .env."
    )


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(_missing_configuration_message())

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def assert_supabase_ready() -> None:
    """Fail fast on startup if Supabase/table configuration is invalid."""
    client = get_supabase_client()
    try:
        client.table(TRANSACTIONS_TABLE).select("id").limit(1).execute()
    except APIError as exc:
        error_code = getattr(exc, "code", "")
        error_text = str(exc)
        if error_code == "PGRST205" or "schema cache" in error_text.lower():
            raise RuntimeError(
                "Supabase table '"
                f"{TRANSACTIONS_TABLE}"
                "' does not exist in this project. "
                "Apply configs/supabase_transactions_patch.sql (or full configs/supabase_schema.sql) "
                "in Supabase SQL Editor, then restart services."
            ) from exc
        raise RuntimeError(
            "Supabase is reachable but data-service readiness check failed. "
            "Verify SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY and table permissions."
        ) from exc
