```python
"""
Wishcode Governed MCP Gateway
=============================

Decision-Artifact Architecture

    Model Proposal
          ↓
       Identity
          ↓
        Request
          ↓
        Policy
          ↓
    Decision Inputs
          ↓
   Governance Decision
          ↓
      Authorization
          ↓
       Execution
          ↓
        Result
          ↓
      Provenance

Core doctrine:

    Myth decides. Math precises. System endures.

Authority doctrine:

    The external model may propose an action.
    The model does not authorize the action.

    MCP establishes connectivity.
    Wishcode establishes authority.
    Policy decides.
    Execution obeys.
    The ledger remembers.

Traceable lineage:

    Canonical DNA
        →
    Wishcode Identity
        →
    Request
        →
    Input Provenance
        →
    Decision Artifact
        →
    Execution
        →
    Result

Current implementation:

    READ_ONLY

Mutation proposals may be observed, evaluated, recorded, and rejected.
They are never executed by this gateway.

IMPORTANT
---------
The MCP server does not create or assign a user's Wishcode identity.

Operational Wishcode identity belongs to the Wishcode application /
subscription boundary.

Example:

    Δ42-B.755.0D27.CLASS-ZERO-ORBIT

is an example operational identity only.

It is NOT hard-coded as the identity of all users.

Canonical architectural identity:

    Δ42:∞BΔ
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from mcp.server import MCPServer
from mcp.server.context import ServerRequestContext


# ============================================================================
# CANONICAL ARCHITECTURE
# ============================================================================

CANONICAL_DNA = "Δ42:∞BΔ"

WISHCODE_PRODUCT = "https://wishcode.co"

POLICY_VERSION = "wishcode-policy-v0.2"

EXECUTION_MODE = "READ_ONLY"


# ============================================================================
# LOGGING
# ============================================================================

# MCP stdio reserves stdout for protocol traffic.
# Python logging therefore remains on stderr.

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger("wishcode.mcp")


# ============================================================================
# CAPABILITY MODEL
# ============================================================================

CAPABILITY_READ = "READ"
CAPABILITY_PROPOSE = "PROPOSE"
CAPABILITY_EXECUTE = "EXECUTE"


MUTATION_CLASSES = {
    "CREATE": CAPABILITY_EXECUTE,
    "UPDATE": CAPABILITY_EXECUTE,
    "DELETE": CAPABILITY_EXECUTE,
    "SUBMIT": CAPABILITY_EXECUTE,
    "COMMIT": CAPABILITY_EXECUTE,
    "EXECUTE": CAPABILITY_EXECUTE,
}


# ============================================================================
# EXTERNAL SYSTEM — READ-ONLY REFERENCE
# ============================================================================

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


# ============================================================================
# IDENTITY
# ============================================================================

@dataclass(frozen=True)
class WishcodeIdentity:
    """
    Operational identity established by the Wishcode application.

    The MCP gateway consumes this identity.

    It does NOT generate the identity.
    """

    wishcode_id: str
    canonical_dna: str = CANONICAL_DNA


class WishcodeIdentityProvider:
    """
    Boundary between the Wishcode application and MCP.

    Production responsibility:

        Wishcode App / Subscription
                ↓
        Authenticated identity
                ↓
        MCP Gateway

    This implementation uses a development context until the
    production Wishcode identity/session API is connected.
    """

    def resolve(
        self,
        identity_context: Mapping[str, Any],
    ) -> WishcodeIdentity:

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

        if not wishcode_id.strip():
            raise ValueError(
                "Wishcode identity cannot be empty"
            )

        if canonical_dna != CANONICAL_DNA:
            raise ValueError(
                "Canonical DNA mismatch"
            )

        return WishcodeIdentity(
            wishcode_id=wishcode_id,
            canonical_dna=canonical_dna,
        )


identity_provider = WishcodeIdentityProvider()


def get_identity_context() -> Mapping[str, Any]:
    """
    Development identity boundary.

    IMPORTANT:

    This is intentionally NOT identity generation.

    The production Wishcode application/session layer should
    supply the authenticated operational identity here.

    Do not replace this with random identity generation.
    """

    return {
        "wishcode_id": (
            "DEVELOPMENT-IDENTITY-NOT-FOR-PRODUCTION"
        ),
        "canonical_dna": CANONICAL_DNA,
        "identity_source": WISHCODE_PRODUCT,
    }


# ============================================================================
# REQUEST / PROPOSAL MODELS
# ============================================================================

@dataclass(frozen=True)
class ModelProposal:
    """
    Represents what the external model proposed.

    Proposal ≠ authorization.
    """

    proposed: bool
    model: str
    requested_action: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class DecisionInputs:
    """
    Inputs independently evaluated by the governance layer.
    """

    execution_mode: str
    capability_class: str
    mutation_class: str
    policy_version: str
    canonical_dna: str
    wishcode_identity_present: bool
    input_fingerprint: str


@dataclass(frozen=True)
class GovernanceDecision:
    """
    Independent governance result.

    This is the authority decision.

    It is not supplied by the model.
    """

    decision: str
    authorized: bool
    reason: str
    policy_version: str


@dataclass(frozen=True)
class ExecutionResult:
    """
    Records what actually happened after authorization.

    For a rejected action:

        tool_invoked = False
        state_transition = NONE
    """

    tool_invoked: bool
    state_transition: str
    result_status: str
    result: Any | None


@dataclass(frozen=True)
class DecisionArtifact:
    """
    First-class governance artifact.

    This is the central object of the revised architecture.

    It preserves:

        Identity
        Request
        Model Proposal
        Input Provenance
        Policy Context
        Decision Inputs
        Governance Decision
        Authorization
        Execution
        Result
    """

    decision_id: str
    request_id: str
    timestamp: str

    canonical_dna: str
    wishcode_identity: str

    model: str

    requested_action: str
    tool_name: str
    arguments: dict[str, Any]

    input_provenance: dict[str, Any]
    input_fingerprint: str

    governance_context: dict[str, Any]
    decision_inputs: dict[str, Any]

    proposed_by_model: bool

    governance_decision: str
    authorized: bool
    authorization_reason: str

    tool_invoked: bool
    state_transition: str

    result_status: str
    result: Any | None

    status: str


# ============================================================================
# FINGERPRINTING
# ============================================================================

def canonical_json(
    value: Any,
) -> str:
    """
    Produce deterministic JSON representation.
    """

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def input_fingerprint(
    value: Any,
) -> str:
    """
    SHA-256 fingerprint of canonical request state.

    This is computational integrity.

    It is NOT:

        - Wishcode identity
        - authentication
        - authorization
    """

    payload = canonical_json(
        value
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


# ============================================================================
# REQUEST VALIDATION
# ============================================================================

RESTRICTED_PATTERNS = (
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bDELETE\s+FROM\b",
)


def validate_request_value(
    value: Any,
) -> None:

    if isinstance(
        value,
        str,
    ):

        for pattern in RESTRICTED_PATTERNS:

            if re.search(
                pattern,
                value,
                flags=re.IGNORECASE,
            ):
                raise ValueError(
                    "Request contains a prohibited pattern"
                )

    elif isinstance(
        value,
        Mapping,
    ):

        for child in value.values():

            validate_request_value(
                child
            )

    elif isinstance(
        value,
        list,
    ):

        for child in value:

            validate_request_value(
                child
            )


# ============================================================================
# GOVERNANCE CORE
# ============================================================================

class WishcodePolicyCore:
    """
    Deterministic governance evaluation.

    The model proposes.

    Policy Core decides.

    The model has no authorization authority.
    """

    def evaluate(
        self,
        *,
        identity: WishcodeIdentity,
        proposal: ModelProposal,
        request_fingerprint: str,
    ) -> tuple[
        DecisionInputs,
        GovernanceDecision,
    ]:

        mutation_class = (
            classify_mutation(
                proposal.tool_name
            )
        )

        capability_class = (
            classify_capability(
                proposal.tool_name
            )
        )

        decision_inputs = DecisionInputs(
            execution_mode=EXECUTION_MODE,
            capability_class=capability_class,
            mutation_class=mutation_class,
            policy_version=POLICY_VERSION,
            canonical_dna=identity.canonical_dna,
            wishcode_identity_present=bool(
                identity.wishcode_id
            ),
            input_fingerprint=request_fingerprint,
        )

        # --------------------------------------------------------------
        # Identity must exist.
        # --------------------------------------------------------------

        if not identity.wishcode_id:

            return (
                decision_inputs,
                GovernanceDecision(
                    decision="DENY",
                    authorized=False,
                    reason=(
                        "Wishcode identity is required"
                    ),
                    policy_version=POLICY_VERSION,
                ),
            )

        # --------------------------------------------------------------
        # Canonical DNA must match.
        # --------------------------------------------------------------

        if identity.canonical_dna != CANONICAL_DNA:

            return (
                decision_inputs,
                GovernanceDecision(
                    decision="DENY",
                    authorized=False,
                    reason=(
                        "Canonical DNA mismatch"
                    ),
                    policy_version=POLICY_VERSION,
                ),
            )

        # --------------------------------------------------------------
        # Mutation is not authorized in READ_ONLY mode.
        # --------------------------------------------------------------

        if capability_class == CAPABILITY_EXECUTE:

            return (
                decision_inputs,
                GovernanceDecision(
                    decision="DENY",
                    authorized=False,
                    reason=(
                        "Mutation not permitted "
                        "under current execution policy"
                    ),
                    policy_version=POLICY_VERSION,
                ),
            )

        # --------------------------------------------------------------
        # READ capability is allowed.
        # --------------------------------------------------------------

        return (
            decision_inputs,
            GovernanceDecision(
                decision="ALLOW",
                authorized=True,
                reason=(
                    "Read capability permitted "
                    "under current execution policy"
                ),
                policy_version=POLICY_VERSION,
            ),
        )


policy_core = WishcodePolicyCore()


# ============================================================================
# CAPABILITY CLASSIFICATION
# ============================================================================

def classify_mutation(
    tool_name: str,
) -> str:

    name = tool_name.lower()

    if name.startswith("create_"):
        return "CREATE"

    if name.startswith("update_"):
        return "UPDATE"

    if name.startswith("delete_"):
        return "DELETE"

    if name.startswith("submit_"):
        return "SUBMIT"

    if name.startswith("commit_"):
        return "COMMIT"

    if name.startswith("execute_"):
        return "EXECUTE"

    return "NONE"


def classify_capability(
    tool_name: str,
) -> str:

    mutation_class = (
        classify_mutation(
            tool_name
        )
    )

    if mutation_class != "NONE":
        return CAPABILITY_EXECUTE

    if tool_name.lower().startswith(
        (
            "prepare_",
            "calculate_",
            "draft_",
            "propose_",
        )
    ):
        return CAPABILITY_PROPOSE

    return CAPABILITY_READ


# ============================================================================
# DECISION ARTIFACT STORE
# ============================================================================

class DecisionArtifactStore:
    """
    Temporary in-memory decision-artifact store.

    Production implementation should persist artifacts into
    the governed State Ledger / provenance subsystem.
    """

    def __init__(self) -> None:

        self._artifacts: list[
            DecisionArtifact
        ] = []

    def append(
        self,
        artifact: DecisionArtifact,
    ) -> None:

        self._artifacts.append(
            artifact
        )

        logger.info(
            (
                "DECISION ARTIFACT | "
                "decision=%s | "
                "request=%s | "
                "wishcode=%s | "
                "tool=%s | "
                "decision=%s | "
                "authorized=%s | "
                "executed=%s"
            ),
            artifact.decision_id,
            artifact.request_id,
            artifact.wishcode_identity,
            artifact.tool_name,
            artifact.governance_decision,
            artifact.authorized,
            artifact.tool_invoked,
        )

    def all(
        self,
    ) -> list[DecisionArtifact]:

        return list(
            self._artifacts
        )


artifact_store = DecisionArtifactStore()


# ============================================================================
# ID GENERATION
# ============================================================================

def generate_request_id() -> str:

    return (
        "REQ-"
        + secrets.token_hex(6).upper()
    )


def generate_decision_id() -> str:

    return (
        "DEC-"
        + secrets.token_hex(6).upper()
    )


# ============================================================================
# PROVENANCE
# ============================================================================

def build_input_provenance(
    *,
    identity: WishcodeIdentity,
    request_id: str,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build provenance describing the input entering governance.

    The actual enterprise asset metadata can be expanded later.
    """

    return {
        "request_id": request_id,
        "canonical_dna": identity.canonical_dna,
        "wishcode_identity": identity.wishcode_id,
        "request_fingerprint": input_fingerprint(
            request
        ),
        "boundary": "MCP_REQUEST",
    }


# ============================================================================
# EXECUTION
# ============================================================================

def execute_read_only_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> ExecutionResult:
    """
    Execute only explicitly supported READ capabilities.

    Mutation tools never reach this function because Policy Core
    denies them before execution.
    """

    if tool_name == "get_trade_status":

        trade_id = arguments.get(
            "trade_id"
        )

        if not isinstance(
            trade_id,
            str,
        ):
            raise ValueError(
                "trade_id must be a string"
            )

        record = TRADE_RECORDS.get(
            trade_id
        )

        if record is None:

            return ExecutionResult(
                tool_invoked=True,
                state_transition="NONE",
                result_status="NOT_FOUND",
                result={
                    "found": False,
                    "trade_id": trade_id,
                },
            )

        return ExecutionResult(
            tool_invoked=True,
            state_transition="NONE",
            result_status="SUCCESS",
            result={
                "found": True,
                "trade": record,
            },
        )

    raise ValueError(
        f"Unsupported read-only tool: {tool_name}"
    )


# ============================================================================
# DECISION ARTIFACT CONSTRUCTION
# ============================================================================

def create_decision_artifact(
    *,
    request_id: str,
    identity: WishcodeIdentity,
    proposal: ModelProposal,
    request: Mapping[str, Any],
    decision_inputs: DecisionInputs,
    governance_decision: GovernanceDecision,
    execution: ExecutionResult,
) -> DecisionArtifact:

    fingerprint = input_fingerprint(
        request
    )

    input_provenance = (
        build_input_provenance(
            identity=identity,
            request_id=request_id,
            request=request,
        )
    )

    governance_context = {
        "policy": "AGENTS.md",
        "policy_version": (
            governance_decision.policy_version
        ),
        "execution_mode": EXECUTION_MODE,
        "authority_boundary": (
            "Wishcode Policy Core"
        ),
    }

    status = (
        "AUTHORIZED"
        if governance_decision.authorized
        else "REJECTED"
    )

    if execution.tool_invoked:
        status = "EXECUTED"

    return DecisionArtifact(
        decision_id=generate_decision_id(),
        request_id=request_id,
        timestamp=datetime.now(
            timezone.utc
        ).isoformat(),

        canonical_dna=identity.canonical_dna,
        wishcode_identity=identity.wishcode_id,

        model=proposal.model,

        requested_action=(
            proposal.requested_action
        ),
        tool_name=proposal.tool_name,
        arguments=proposal.arguments,

        input_provenance=input_provenance,
        input_fingerprint=fingerprint,

        governance_context=governance_context,
        decision_inputs=asdict(
            decision_inputs
        ),

        proposed_by_model=(
            proposal.proposed
        ),

        governance_decision=(
            governance_decision.decision
        ),
        authorized=(
            governance_decision.authorized
        ),
        authorization_reason=(
            governance_decision.reason
        ),

        tool_invoked=(
            execution.tool_invoked
        ),
        state_transition=(
            execution.state_transition
        ),

        result_status=(
            execution.result_status
        ),
        result=execution.result,

        status=status,
    )


# ============================================================================
# MCP SERVER
# ============================================================================

mcp = MCPServer(
    "Wishcode-Decision-Artifact-Gateway",
)


# ============================================================================
# MCP READ TOOL
# ============================================================================

@mcp.tool()
def get_trade_status(
    trade_id: str,
) -> dict[str, Any]:
    """
    READ capability.

    Retrieve the status of a trade.

    Governance occurs before this handler executes.
    """

    validate_request_value(
        trade_id
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


# ============================================================================
# MCP GOVERNANCE RESOURCE
# ============================================================================

@mcp.resource(
    "wishcode://governance/active-policy"
)
def active_policy() -> str:
    """
    Return the active governance configuration.
    """

    identity = identity_provider.resolve(
        get_identity_context()
    )

    return json.dumps(
        {
            "product": WISHCODE_PRODUCT,
            "canonical_dna": (
                CANONICAL_DNA
            ),
            "wishcode_identity": (
                identity.wishcode_id
            ),
            "policy_version": (
                POLICY_VERSION
            ),
            "execution_mode": (
                EXECUTION_MODE
            ),
            "mutation_authorized": False,
            "identity_generation": (
                "WISHCODE_APPLICATION"
            ),
            "authority": (
                "WISHCODE_POLICY_CORE"
            ),
            "lineage": (
                "Identity → Request → "
                "Policy → Decision Inputs → "
                "Governance Decision → "
                "Execution → Result"
            ),
        },
        indent=2,
        ensure_ascii=False,
    )


# ============================================================================
# GOVERNANCE MIDDLEWARE
# ============================================================================

async def governance_middleware(
    ctx: ServerRequestContext[Any, Any],
    call_next,
):
    """
    Governance interception boundary.

    For tools/call:

        Model proposal
              ↓
        Wishcode identity
              ↓
        Request validation
              ↓
        Input fingerprint
              ↓
        Policy evaluation
              ↓
        Decision Artifact
              ↓
        Authorization
              ↓
        Tool execution

    A denied mutation is recorded as a Decision Artifact and
    never reaches execution.
    """

    if ctx.method != "tools/call":

        return await call_next(ctx)

    params = ctx.params

    if not isinstance(
        params,
        Mapping,
    ):
        raise ValueError(
            "Invalid tools/call parameters"
        )

    # ------------------------------------------------------------------
    # REQUEST
    # ------------------------------------------------------------------

    request_id = generate_request_id()

    tool_name = params.get(
        "name"
    )

    if not isinstance(
        tool_name,
        str,
    ):
        raise ValueError(
            "Tool name is required"
        )

    raw_arguments = params.get(
        "arguments",
        {},
    )

    if not isinstance(
        raw_arguments,
        Mapping,
    ):
        raise ValueError(
            "Tool arguments must be an object"
        )

    arguments = dict(
        raw_arguments
    )

    request = {
        "method": ctx.method,
        "request_id": request_id,
        "tool": tool_name,
        "arguments": arguments,
    }

    # ------------------------------------------------------------------
    # MODEL PROPOSAL
    # ------------------------------------------------------------------

    proposal = ModelProposal(
        proposed=True,
        model="External LLM",
        requested_action=(
            f"{tool_name}()"
        ),
        tool_name=tool_name,
        arguments=arguments,
    )

    # ------------------------------------------------------------------
    # IDENTITY
    # ------------------------------------------------------------------

    identity_context = (
        get_identity_context()
    )

    identity = (
        identity_provider.resolve(
            identity_context
        )
    )

    # ------------------------------------------------------------------
    # REQUEST VALIDATION
    # ------------------------------------------------------------------

    validate_request_value(
        request
    )

    # ------------------------------------------------------------------
    # INPUT FINGERPRINT
    # ------------------------------------------------------------------

    fingerprint = input_fingerprint(
        request
    )

    # ------------------------------------------------------------------
    # POLICY EVALUATION
    # ------------------------------------------------------------------

    decision_inputs, governance_decision = (
        policy_core.evaluate(
            identity=identity,
            proposal=proposal,
            request_fingerprint=fingerprint,
        )
    )

    # ------------------------------------------------------------------
    # REJECTED PATH
    # ------------------------------------------------------------------

    if not governance_decision.authorized:

        execution = ExecutionResult(
            tool_invoked=False,
            state_transition="NONE",
            result_status="REJECTED",
            result=None,
        )

        artifact = (
            create_decision_artifact(
                request_id=request_id,
                identity=identity,
                proposal=proposal,
                request=request,
                decision_inputs=decision_inputs,
                governance_decision=(
                    governance_decision
                ),
                execution=execution,
            )
        )

        artifact_store.append(
            artifact
        )

        logger.warning(
            (
                "GOVERNANCE REJECTED | "
                "decision=%s | "
                "request=%s | "
                "tool=%s | "
                "wishcode=%s | "
                "reason=%s"
            ),
            artifact.decision_id,
            request_id,
            tool_name,
            identity.wishcode_id,
            governance_decision.reason,
        )

        raise ValueError(
            "Wishcode governance denied execution: "
            + governance_decision.reason
        )

    # ------------------------------------------------------------------
    # AUTHORIZED PATH
    # ------------------------------------------------------------------

    execution = execute_read_only_tool(
        tool_name,
        arguments,
    )

    # ------------------------------------------------------------------
    # DECISION ARTIFACT
    # ------------------------------------------------------------------

    artifact = (
        create_decision_artifact(
            request_id=request_id,
            identity=identity,
            proposal=proposal,
            request=request,
            decision_inputs=decision_inputs,
            governance_decision=(
                governance_decision
            ),
            execution=execution,
        )
    )

    artifact_store.append(
        artifact
    )

    logger.info(
        (
            "GOVERNANCE EXECUTED | "
            "decision=%s | "
            "request=%s | "
            "tool=%s | "
            "wishcode=%s | "
            "fingerprint=%s | "
            "result=%s"
        ),
        artifact.decision_id,
        request_id,
        tool_name,
        identity.wishcode_id,
        fingerprint,
        execution.result_status,
    )

    return await call_next(ctx)


# ============================================================================
# ATTACH GOVERNANCE MIDDLEWARE
# ============================================================================

mcp.middleware.append(
    governance_middleware
)


# ============================================================================
# ENTRY POINT
# ============================================================================

def main() -> None:
    """
    Start the governed MCP server.

    stdout is reserved for MCP protocol traffic.
    """

    logger.info(
        (
            "Wishcode Decision-Artifact Gateway starting | "
            "product=%s | "
            "dna=%s | "
            "policy=%s | "
            "mode=%s"
        ),
        WISHCODE_PRODUCT,
        CANONICAL_DNA,
        POLICY_VERSION,
        EXECUTION_MODE,
    )

    mcp.run(
        transport="stdio"
    )


if __name__ == "__main__":
    main()
```
