# Wishcode MCP (DLX-MCP)

**`DecisionArtifact`** — implemented as a `frozen=True` Python dataclass.

A data packet is still bytes, but its authority is not allowed to float without provenance.

## Purpose

Shifting the Balance of Power.

The Wishcode MCP layer establishes standardized connectivity between compatible AI agents and external systems, tools, and data sources.

MCP provides the connectivity interface.

Wishcode retains governance and execution authority.

## Architectural Position

```text
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
Policy / Authorization
    ↓
Deterministic Execution
    ↓
Provenance
```

## Principle

**AGENTS.md establishes context.**

**MCP establishes connectivity.**

**Wishcode establishes authority.**

## Authority Boundary

MCP tools must not independently authorize consequential execution.

External tool access is subject to the applicable Wishcode validation, governance, authorization, and execution controls.

A model, agent, MCP tool, connector, or external service must not become an independent execution authority.

## Initial Development Strategy

The first MCP implementation will expose read-only capabilities.

Initial capability classes:

* Trade information retrieval
* Invoice retrieval
* Bill of lading retrieval
* Compliance-status retrieval

Mutation and execution capabilities will be introduced only after the corresponding validation and authorization architecture is implemented.

## Design Objective

The MCP layer should remain replaceable.

The underlying model may change.

The compatible agent may change.

The external system may change.

The connectivity protocol may evolve.

The Wishcode governance boundary remains the controlling architectural layer.
