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
    Wishcode App
        ↓
    Wishcode Operational Identity
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

Identity Architecture
---------------------
Canonical architectural identity:

    Δ42:∞BΔ

This is the Multiverse DNA / canonical architectural fingerprint.

Operational Wishcode identities are established by the Wishcode
application/subscription system.

Example only:

    Δ42-B.755.0D27.CLASS-ZERO-ORBIT

The example above is NOT hard-coded as a product identity.

Wishcode may contain millions of independent operational identities.

The MCP gateway does NOT generate, assign, or derive a user's
Wishcode identity.

It receives an already-established identity context from the
Wishcode application boundary.

Traceable Lineage
-----------------
Canonical DNA
    ↓
Operational Wishcode Identity
    ↓
MCP Request
    ↓
Input Fingerprint
    ↓
Governance Decision
    ↓
Provenance Record

Identity and computational state are deliberately separated:

    Wishcode ID
        = operational identity / lineage

    Input Fingerprint
        = deterministic fingerprint of request state

The two are bound together in provenance.

Important
---------
This implementation is the first identity-aware, read-only MCP
gateway milestone.

It intentionally does NOT implement:

- identity generation
- subscription issuance
- production authentication
- cryptographic authorization artifacts
- human-in-the-loop approval
- mutation execution
- immutable external ledger persistence
- downstream MCP proxying

Those belong to later architectural stages.

MCP establishes connectivity.
Wishcode establishes identity.
Wishcode establishes authority.
The fingerprint establishes computational state.
Policy decides.
Execution obeys.
The ledger remembers.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from mcp.server import MCPServer
from mcp.server.context import ServerRequestContext


# ===========================================================================
# CANONICAL WISHCODE ARCHITECTURE
# ===========================================================================

CANONICAL_DNA = "Δ42:∞BΔ"

WISHCODE_PRODUCT_ORIGIN = "https://wishcode.co"


# ===========================================================================
# LOGGING
# ===========================================================================
#
# MCP stdio transport uses stdout for protocol traffic.
# Logging therefore remains on stderr through Python logging.
#

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("wishcode.mcp")


# ===========================================================================
# MOCK EXTERNAL SYSTEM
# ===========================================================================
#
# This represents an external enterprise capability.
# It is intentionally READ-ONLY for the first implementation.
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


# ===========================================================================
# IDENTITY / GOVERNANCE DATA STRUCTURES
# ===========================================================================

@dataclass(frozen=True)
class WishcodeIdentity:
    """
    Established operational Wishcode identity.

    IMPORTANT:
    The MCP gateway consumes this identity.

    It does NOT generate it.

    Identity issuance belongs to the Wishcode application /
    subscription boundary.
    """

    wishcode_id: str

    canonical_dna: str = CANONICAL_DNA


@dataclass(frozen=True)
class GovernanceDecision:
    """
    Result of the current Wishcode governance evaluation.

    This is a policy decision representation.

    It is NOT a cryptographic authorization artifact.
    """

    decision: str
    reason: str
    policy_version: str


@dataclass(frozen=True)
class ProvenanceRecord:
    """
    Traceable lineage record for one governed MCP event.

    Identity:

        wishcode_id

    Canonical architecture:

        canonical_dna

    Computational state:

        input_hash

    Governance:

        decision + policy_version
    """

    provenance_id: str
    timestamp: str

    canonical_dna: str
    wishcode_id: str

    method: str
    tool: str | None

    input_hash: str

    decision: str
    policy_version: str


# ===========================================================================
# POLICY CONFIGURATION
# ===========================================================================

POLICY_VERSION = "wishcode-policy-v0.1"


# Restricted patterns are deliberately conservative.
# They are NOT presented as a complete security policy.

RESTRICTED_PATTERNS = (
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bDELETE\s+FROM\b",
    r";\s*$",
)


# ===========================================================================
# UTILITY FUNCTIONS
# ===========================================================================

def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    """
    Serialize a value deterministically.

    This creates the canonical representation used for
    computational fingerprinting.
    """

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def stable_input_fingerprint(value: Any) -> str:
    """
    Create a deterministic computational fingerprint of request state.

    IMPORTANT:

    This is NOT the user's Wishcode identity.

    This is NOT the Wishcode subscription fingerprint.

    This is NOT an authorization credential.

    It identifies the exact canonicalized request state that
    participated in the governed event.
    """

    payload = canonical_json(value).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def validate_string(
    value: str,
    field_name: str,
) -> None:
    """
    Basic deterministic input validation.

    MCP/Pydantic provides structural type validation.

    This function provides additional domain-level validation.
    """

    if not value.strip():
        raise ValueError(
            f"{field_name} must not be empty"
        )

    for pattern in RESTRICTED_PATTERNS:
        if re.search(
            pattern,
            value,
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                f"{field_name} contains a prohibited pattern"
            )


# ===========================================================================
# WISHCODE IDENTITY VALIDATION
# ===========================================================================

def validate_wishcode_identity(
    identity: WishcodeIdentity,
) -> None:
    """
    Validate the structural identity context.

    This function does NOT issue an identity.

    It does NOT determine subscription ownership.

    It does NOT replace production authentication.

    It only verifies that an already-established identity is
    structurally bound to the canonical Wishcode architecture.
    """

    if not identity.wishcode_id.strip():
        raise ValueError(
            "Wishcode operational identity is required"
        )

    if identity.canonical_dna != CANONICAL_DNA:
        raise ValueError(
            "Wishcode identity is bound to invalid canonical DNA"
        )


# ===========================================================================
# WISHCODE IDENTITY PROVIDER BOUNDARY
# ===========================================================================

class WishcodeIdentityProvider:
    """
    Boundary between the Wishcode application and the MCP gateway.

    The important architectural rule is:

        MCP does not generate identity.

        Wishcode establishes identity.

    The provider is therefore intentionally an interface boundary.

    A production implementation can later connect this provider
    to the authenticated Wishcode application/session/subscription
    service without changing the governance architecture.
    """

    def get_active_identity(
        self,
        identity_context: Mapping[str, Any],
    ) -> WishcodeIdentity:
        """
        Resolve the already-established Wishcode identity.

        Expected identity_context shape:

            {
                "wishcode_id": "...",
                "canonical_dna": "Δ42:∞BΔ"
            }

        The actual authentication/subscription mechanism belongs
        to the Wishcode application layer.
        """

        wishcode_id = identity_context.get(
            "wishcode_id"
        )

        canonical_dna = identity_context.get(
            "canonical_dna",
            CANONICAL_DNA,
        )

        if not isinstance(
            wishcode_id,
            str,
        ):
            raise ValueError(
                "Authenticated Wishcode identity is missing"
            )

        if not isinstance(
            canonical_dna,
            str,
        ):
            raise ValueError(
                "Canonical DNA is invalid"
            )

        identity = WishcodeIdentity(
            wishcode_id=wishcode_id,
            canonical_dna=canonical_dna,
        )

        validate_wishcode_identity(identity)

        return identity


# ===========================================================================
# DEVELOPMENT IDENTITY CONTEXT
# ===========================================================================
#
# DEVELOPMENT ONLY.
#
# This represents an identity that has ALREADY been established by
# the Wishcode application.
#
# It is NOT generated by the MCP server.
#
# Replace this boundary with the real authenticated application/session
# context when the Wishcode identity API is connected.
#

def get_identity_context() -> Mapping[str, Any]:
    """
    Return the established Wishcode identity context.

    Development placeholder only.

    IMPORTANT:

    The value below represents an external identity supplied to
    the gateway.

    The MCP gateway does not generate the identity.

    The production implementation should obtain this context from
    the authenticated Wishcode application/session boundary.
    """

    return {
        "wishcode_id": (
            "DEVELOPMENT-IDENTITY-NOT-FOR-PRODUCTION"
        ),
        "canonical_dna": CANONICAL_DNA,
        "identity_source": WISHCODE_PRODUCT_ORIGIN,
    }


# ===========================================================================
# GOVERNANCE BOUNDARY
# ===========================================================================

class WishcodeGovernance:
    """
    Identity-aware governance boundary.

    Architectural flow:

        Wishcode Identity
                ↓
            MCP Request
                ↓
        Request Validation
                ↓
          Policy Evaluation
                ↓
       Computational Fingerprint
                ↓
           Provenance
                ↓
          Tool Execution

    Future versions will separate:

    - Policy Core
    - identity authentication
    - subscription verification
    - authorization artifacts
    - execution sigils
    - HITL approval
    - immutable State Ledger
    """

    def __init__(self) -> None:
        self.provenance_records: list[
            ProvenanceRecord
        ] = []

    def validate_identity(
        self,
        identity: WishcodeIdentity,
    ) -> None:
        """
        Validate established identity context.
        """

        validate_wishcode_identity(identity)

    def validate_request(
        self,
        method: str,
        params: Mapping[str, Any] | None,
    ) -> None:
        """
        Validate the inbound MCP request before execution.
        """

        if not method:
            raise ValueError(
                "MCP method is required"
            )

        if params is None:
            return

        for key, value in params.items():

            if isinstance(
                value,
                str,
            ):
                validate_string(
                    value,
                    key,
                )

    def evaluate_policy(
        self,
        identity: WishcodeIdentity,
        tool_name: str,
        params: dict[str, Any],
    ) -> GovernanceDecision:
        """
        Evaluate the current read-only policy.

        Current policy:

            Valid Wishcode identity
                    +
              READ capability
                    ↓
                 ALLOW

        Mutation capability is not enabled in this gateway.
        """

        if not identity.wishcode_id:
            return GovernanceDecision(
                decision="DENY",
                reason="Wishcode identity missing",
                policy_version=POLICY_VERSION,
            )

        if identity.canonical_dna != CANONICAL_DNA:
            return GovernanceDecision(
                decision="DENY",
                reason="Canonical DNA mismatch",
                policy_version=POLICY_VERSION,
            )

        if not tool_name:
            return GovernanceDecision(
                decision="DENY",
                reason="Tool identity missing",
                policy_version=POLICY_VERSION,
            )

        mutation_prefixes = (
            "create_",
            "update_",
            "delete_",
            "submit_",
            "execute_",
            "commit_",
            "approve_",
        )

        if tool_name.lower().startswith(
            mutation_prefixes
        ):
            return GovernanceDecision(
                decision="DENY",
                reason=(
                    "Mutation capability is not enabled "
                    "in read-only gateway"
                ),
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
        identity: WishcodeIdentity,
        method: str,
        tool_name: str | None,
        params: Any,
        decision: GovernanceDecision,
    ) -> ProvenanceRecord:
        """
        Record one traceable lineage event.

        Current implementation is in-memory.

        The production State Ledger will replace this mechanism.

        Lineage:

            Δ42:∞BΔ
                ↓
            Wishcode ID
                ↓
            Input Fingerprint
                ↓
            Governance Decision
                ↓
            Provenance ID
        """

        input_hash = stable_input_fingerprint(
            params
        )

        record = ProvenanceRecord(
            provenance_id=(
                f"wc_prov_{secrets.token_hex(12)}"
            ),
            timestamp=utc_timestamp(),

            canonical_dna=identity.canonical_dna,
            wishcode_id=identity.wishcode_id,

            method=method,
            tool=tool_name,

            input_hash=input_hash,

            decision=decision.decision,
            policy_version=decision.policy_version,
        )

        self.provenance_records.append(
            record
        )

        logger.info(
            (
                "PROVENANCE | "
                "dna=%s | "
                "wishcode=%s | "
                "provenance=%s | "
                "method=%s | "
                "tool=%s | "
                "input=%s | "
                "decision=%s"
            ),
            record.canonical_dna,
            record.wishcode_id,
            record.provenance_id,
            record.method,
            record.tool,
            record.input_hash,
            record.decision,
        )

        return record


# ===========================================================================
# GOVERNANCE INSTANCE
# ===========================================================================

identity_provider = (
    WishcodeIdentityProvider()
)

governance = WishcodeGovernance()


# ===========================================================================
# MCP MIDDLEWARE
# ===========================================================================

async def wishcode_governance_middleware(
    ctx: ServerRequestContext[Any, Any],
    call_next,
):
    """
    Intercept inbound MCP messages.

    For tools/call:

        1. obtain established Wishcode identity
        2. validate identity
        3. inspect MCP request
        4. validate request
        5. identify tool
        6. evaluate policy
        7. fingerprint request state
        8. record traceable lineage
        9. allow or refuse execution

    The middleware does NOT create a Wishcode identity.
    """

    method = ctx.method
    params = ctx.params

    # ------------------------------------------------------------------
    # Non-tool messages
    # ------------------------------------------------------------------

    if method != "tools/call":
        return await call_next(ctx)

    tool_name: str | None = None

    if isinstance(
        params,
        Mapping,
    ):
        raw_name = params.get(
            "name"
        )

        if isinstance(
            raw_name,
            str,
        ):
            tool_name = raw_name

    try:

        # --------------------------------------------------------------
        # 1. Obtain established identity context
        # --------------------------------------------------------------

        identity_context = (
            get_identity_context()
        )

        # --------------------------------------------------------------
        # 2. Resolve identity through application boundary
        # --------------------------------------------------------------

        identity = (
            identity_provider.get_active_identity(
                identity_context
            )
        )

        # --------------------------------------------------------------
        # 3. Validate MCP request
        # --------------------------------------------------------------

        governance.validate_request(
            method,
            params,
        )

        # --------------------------------------------------------------
        # 4. Extract tool arguments
        # --------------------------------------------------------------

        tool_params: dict[
            str,
            Any,
        ] = {}

        if isinstance(
            params,
            Mapping,
        ):

            arguments = params.get(
                "arguments"
            )

            if isinstance(
                arguments,
                Mapping,
            ):
                tool_params = dict(
                    arguments
                )

        # --------------------------------------------------------------
        # 5. Evaluate policy
        # --------------------------------------------------------------

        decision = (
            governance.evaluate_policy(
                identity=identity,
                tool_name=tool_name or "",
                params=tool_params,
            )
        )

        # --------------------------------------------------------------
        # 6. Record traceable lineage
        # --------------------------------------------------------------

        record = (
            governance.record_provenance(
                identity=identity,
                method=method,
                tool_name=tool_name,
                params=params,
                decision=decision,
            )
        )

        # --------------------------------------------------------------
        # 7. Enforce governance decision
        # --------------------------------------------------------------

        if decision.decision != "ALLOW":

            raise ValueError(
                "Wishcode governance denied "
                f"tool execution: {decision.reason}"
            )

        logger.info(
            (
                "GOVERNANCE ALLOW | "
                "dna=%s | "
                "wishcode=%s | "
                "tool=%s | "
                "provenance=%s | "
                "input=%s | "
                "policy=%s"
            ),
            identity.canonical_dna,
            identity.wishcode_id,
            tool_name,
            record.provenance_id,
            record.input_hash,
            record.policy_version,
        )

    except Exception as exc:

        logger.warning(
            (
                "GOVERNANCE DENY | "
                "method=%s | "
                "tool=%s | "
                "reason=%s"
            ),
            method,
            tool_name,
            exc,
        )

        raise

    return await call_next(ctx)


# ===========================================================================
# MCP SERVER
# ===========================================================================

mcp = MCPServer(
    "Wishcode-Governed-MCP-Gateway",
    middleware=[
        wishcode_governance_middleware
    ],
)


# ===========================================================================
# READ-ONLY MCP CAPABILITY
# ===========================================================================

@mcp.tool()
def get_trade_status(
    trade_id: str,
) -> dict[str, Any]:
    """
    Retrieve trade status from the external capability layer.

    Capability class:
        READ

    This tool does not mutate enterprise state.
    """

    validate_string(
        trade_id,
        "trade_id",
    )

    record = TRADE_RECORDS.get(
        trade_id
    )

    if record is None:

        return {
            "found": False,
            "trade_id": trade_id,
        }

    return {
        "found": True,
        "trade": record,
    }


# ===========================================================================
# GOVERNANCE RESOURCE
# ===========================================================================

@mcp.resource(
    "wishcode://governance/active-policy"
)
def active_policy() -> str:
    """
    Expose active governance metadata.

    This resource is informational only.
    """

    identity_context = (
        get_identity_context()
    )

    identity = (
        identity_provider.get_active_identity(
            identity_context
        )
    )

    return json.dumps(
        {
            "system": "Wishcode",

            "product": WISHCODE_PRODUCT_ORIGIN,

            "canonical_dna": (
                CANONICAL_DNA
            ),

            "wishcode_identity": (
                identity.wishcode_id
            ),

            "identity_source": (
                WISHCODE_PRODUCT_ORIGIN
            ),

            "identity_generation": (
                "NOT_PERFORMED_BY_MCP"
            ),

            "policy_version": (
                POLICY_VERSION
            ),

            "capability_mode": (
                "READ_ONLY"
            ),

            "mutation_execution": False,

            "authority_boundary": (
                "Wishcode Governance Boundary"
            ),

            "lineage_model": (
                "Canonical DNA → "
                "Wishcode Identity → "
                "Input Fingerprint → "
                "Governance → "
                "Provenance"
            ),

            "principle": (
                "MCP establishes connectivity. "
                "Wishcode establishes authority."
            ),
        },
        indent=2,
        ensure_ascii=False,
    )


# ===========================================================================
# SERVER ENTRY POINT
# ===========================================================================

def main() -> None:
    """
    Start the MCP server using stdio transport.

    stdout remains reserved for MCP protocol traffic.
    """

    logger.info(
        (
            "Starting Wishcode Governed MCP Gateway | "
            "product=%s | "
            "dna=%s | "
            "policy=%s"
        ),
        WISHCODE_PRODUCT_ORIGIN,
        CANONICAL_DNA,
        POLICY_VERSION,
    )

    mcp.run(
        transport="stdio"
    )


if __name__ == "__main__":
    main()
```
