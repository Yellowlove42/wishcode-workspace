```python
"""
Wishcode Governed MCP Gateway
=============================

Purpose
-------
Establish MCP connectivity while keeping governance and execution
authority inside the Wishcode boundary.

Architectural principle:

    AGENTS.md
        ↓
    Governance Context
        ↓
    MCP
        ↓
    Connectivity
        ↓
    Wishcode Governance Boundary
        ↓
    Policy Evaluation
        ↓
    Deterministic Execution
        ↓
    Provenance

Important
---------
This implementation is the first read-only gateway milestone.

It intentionally does NOT implement:

- cryptographic authorization artifacts
- human-in-the-loop approval
- mutation execution
- immutable external ledger persistence
- downstream MCP proxying
- production identity/authentication

Those belong to later architectural stages.

MCP establishes connectivity.
Wishcode establishes authority.
Policy decides.
Execution obeys.
The ledger remembers.
"""

from __future__ import annotations

import json
import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from mcp.server import MCPServer
from mcp.server.context import ServerRequestContext


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
#
# MCP stdio transports use stdout for protocol traffic.
# Logging therefore remains on stderr through Python's logging system.
#

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("wishcode.mcp")


# ---------------------------------------------------------------------------
# Mock external system
# ---------------------------------------------------------------------------
#
# This represents an external enterprise capability.
# It is intentionally read-only for the first implementation.
#

TRADE_RECORDS: dict[str, dict[str, Any]] = {
    "TRD-001": {
        "trade_id": "TRD-001",
        "status": "IN_TRANSIT",
        "origin": "Kolkata",
        "destination": "Dubai",
        "invoice_id": "INV-1001",
        "bill_of_lading": "BL-7001",
    },
    "TRD-002": {
        "trade_id": "TRD-002",
        "status": "CUSTOMS_REVIEW",
        "origin": "Mumbai",
        "destination": "Singapore",
        "invoice_id": "INV-1002",
        "bill_of_lading": "BL-7002",
    },
}


# ---------------------------------------------------------------------------
# Governance data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GovernanceDecision:
    """
    Result of the current Wishcode governance evaluation.

    This is intentionally simple.

    It is NOT yet a cryptographic authorization artifact.
    """

    decision: str
    reason: str
    policy_version: str


@dataclass(frozen=True)
class ProvenanceRecord:
    """
    Temporary provenance representation.

    Later versions should persist this into the Wishcode State Ledger
    with immutable lineage and cryptographic integrity.
    """

    provenance_id: str
    timestamp: str
    method: str
    tool: str | None
    input_hash: str
    decision: str
    policy_version: str


# ---------------------------------------------------------------------------
# Policy configuration
# ---------------------------------------------------------------------------

POLICY_VERSION = "wishcode-policy-v0.1"

# Restricted patterns are deliberately conservative.
# They are not presented as a complete security policy.
RESTRICTED_PATTERNS = (
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bDELETE\s+FROM\b",
    r";\s*$",
)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    """Return deterministic JSON suitable for hashing."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def stable_input_fingerprint(value: Any) -> str:
    """
    Create a deterministic fingerprint of request input.

    This is a provenance aid only.

    It is NOT being presented as a cryptographic authorization mechanism.
    """
    import hashlib

    payload = canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_string(value: str, field_name: str) -> None:
    """
    Basic deterministic input validation.

    MCP/Pydantic provides structural type validation.
    This function provides additional domain-level validation.
    """

    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")

    for pattern in RESTRICTED_PATTERNS:
        if re.search(pattern, value, flags=re.IGNORECASE):
            raise ValueError(
                f"{field_name} contains a prohibited pattern"
            )


# ---------------------------------------------------------------------------
# Wishcode Governance Boundary
# ---------------------------------------------------------------------------

class WishcodeGovernance:
    """
    Minimal governance boundary for the first MCP implementation.

    Architectural role:

        MCP request
             ↓
        Schema/domain validation
             ↓
        Policy evaluation
             ↓
        Provenance
             ↓
        Tool handler

    Future versions will separate Policy Core, authorization artifacts,
    execution sigils, HITL approval, and State Ledger persistence.
    """

    def __init__(self) -> None:
        self.provenance_records: list[ProvenanceRecord] = []

    def validate_request(
        self,
        method: str,
        params: Any,
    ) -> None:
        """
        Validate the inbound MCP request before execution.
        """

        if not method:
            raise ValueError("MCP method is required")

        # Defensive validation of raw request parameters.
        if params is None:
            return

        if isinstance(params, dict):
            for key, value in params.items():
                if isinstance(value, str):
                    validate_string(value, key)

    def evaluate_policy(
        self,
        tool_name: str,
        params: dict[str, Any],
    ) -> GovernanceDecision:
        """
        Evaluate the current read-only policy.

        Current policy:

        READ operations may proceed.

        No mutation capability is exposed by this server.
        """

        if not tool_name:
            return GovernanceDecision(
                decision="DENY",
                reason="Tool identity missing",
                policy_version=POLICY_VERSION,
            )

        # Explicitly deny mutation-style tool naming in this first gateway.
        mutation_prefixes = (
            "create_",
            "update_",
            "delete_",
            "submit_",
            "execute_",
            "commit_",
            "approve_",
        )

        if tool_name.lower().startswith(mutation_prefixes):
            return GovernanceDecision(
                decision="DENY",
                reason="Mutation capability is not enabled in read-only gateway",
                policy_version=POLICY_VERSION,
            )

        return GovernanceDecision(
            decision="ALLOW",
            reason="Read-only capability permitted",
            policy_version=POLICY_VERSION,
        )

    def record_provenance(
        self,
        *,
        method: str,
        tool_name: str | None,
        params: Any,
        decision: GovernanceDecision,
    ) -> ProvenanceRecord:
        """
        Record the governance event.

        This is currently in-memory.

        The production State Ledger will replace this mechanism.
        """

        record = ProvenanceRecord(
            provenance_id=f"wc_prov_{secrets.token_hex(12)}",
            timestamp=utc_timestamp(),
            method=method,
            tool=tool_name,
            input_hash=stable_input_fingerprint(params),
            decision=decision.decision,
            policy_version=decision.policy_version,
        )

        self.provenance_records.append(record)

        logger.info(
            "PROVENANCE | id=%s | method=%s | tool=%s | decision=%s",
            record.provenance_id,
            record.method,
            record.tool,
            record.decision,
        )

        return record


# ---------------------------------------------------------------------------
# Governance instance
# ---------------------------------------------------------------------------

governance = WishcodeGovernance()


# ---------------------------------------------------------------------------
# MCP Middleware
# ---------------------------------------------------------------------------

async def wishcode_governance_middleware(
    ctx: ServerRequestContext[Any, Any],
    call_next,
):
    """
    Intercept every inbound MCP message.

    Important:

        MCP middleware is a governance interception point.

    It is NOT the final Wishcode Policy Core.

    For tools/call requests we:

        1. inspect the request
        2. validate raw parameters
        3. identify the requested tool
        4. evaluate current policy
        5. record provenance
        6. allow or refuse the request

    No mutation capability is exposed yet.
    """

    method = ctx.method
    params = ctx.params

    # The middleware observes every MCP message.
    # Only tools/call receives the first governance enforcement path.
    if method != "tools/call":
        return await call_next(ctx)

    tool_name: str | None = None

    if isinstance(params, dict):
        raw_name = params.get("name")

        if isinstance(raw_name, str):
            tool_name = raw_name

    try:
        # ---------------------------------------------------------------
        # 1. Deterministic request validation
        # ---------------------------------------------------------------

        governance.validate_request(method, params)

        # ---------------------------------------------------------------
        # 2. Policy evaluation
        # ---------------------------------------------------------------

        tool_params: dict[str, Any] = {}

        if isinstance(params, dict):
            arguments = params.get("arguments")

            if isinstance(arguments, dict):
                tool_params = arguments

        decision = governance.evaluate_policy(
            tool_name or "",
            tool_params,
        )

        # ---------------------------------------------------------------
        # 3. Provenance recording
        # ---------------------------------------------------------------

        record = governance.record_provenance(
            method=method,
            tool_name=tool_name,
            params=params,
            decision=decision,
        )

        # ---------------------------------------------------------------
        # 4. Governance decision
        # ---------------------------------------------------------------

        if decision.decision != "ALLOW":
            raise ValueError(
                f"Wishcode governance denied tool execution: "
                f"{decision.reason}"
            )

        logger.info(
            "GOVERNANCE ALLOW | tool=%s | provenance=%s | policy=%s",
            tool_name,
            record.provenance_id,
            decision.policy_version,
        )

    except Exception as exc:
        logger.warning(
            "GOVERNANCE DENY | method=%s | tool=%s | reason=%s",
            method,
            tool_name,
            exc,
        )
        raise

    return await call_next(ctx)


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = MCPServer(
    "Wishcode-Governed-MCP-Gateway",
    middleware=[wishcode_governance_middleware],
)


# ---------------------------------------------------------------------------
# Read-only MCP capability
# ---------------------------------------------------------------------------

@mcp.tool()
def get_trade_status(trade_id: str) -> dict[str, Any]:
    """
    Retrieve trade status from the external capability layer.

    Capability class:
        READ

    This tool does not mutate enterprise state.
    """

    validate_string(trade_id, "trade_id")

    record = TRADE_RECORDS.get(trade_id)

    if record is None:
        return {
            "found": False,
            "trade_id": trade_id,
        }

    return {
        "found": True,
        "trade": record,
    }


# ---------------------------------------------------------------------------
# Governance resource
# ---------------------------------------------------------------------------

@mcp.resource("wishcode://governance/active-policy")
def active_policy() -> str:
    """
    Expose the currently active governance policy metadata.

    This is informational only.
    """

    return json.dumps(
        {
            "system": "Wishcode",
            "policy_version": POLICY_VERSION,
            "capability_mode": "READ_ONLY",
            "mutation_execution": False,
            "authority_boundary": "Wishcode Governance Boundary",
            "principle": (
                "MCP establishes connectivity. "
                "Wishcode establishes authority."
            ),
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Start the MCP server using stdio transport.

    stdout remains reserved for MCP protocol traffic.
    """

    logger.info(
        "Starting Wishcode Governed MCP Gateway | policy=%s",
        POLICY_VERSION,
    )

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```
