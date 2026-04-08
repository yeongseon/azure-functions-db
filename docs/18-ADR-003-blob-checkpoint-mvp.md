# ADR-003: Blob Storage as MVP Checkpoint Store

## Status
Accepted

## Context

The checkpoint/lease store must be easy to provision in an Azure environment and have low
operational overhead.

## Decision

The default checkpoint/lease store for the MVP is Azure Blob Storage.

## Rationale

- Works naturally with Azure Functions
- Already present in most environments
- JSON blob inspection is straightforward
- Cost and simplicity are appropriate

## Drawbacks
- No advanced query/search capabilities
- Custom logic required if lease primitives are not used directly
- Table Storage or Cosmos DB may be more suitable for large-scale multi-poller scenarios

## Follow-up
Consider adding Table/Cosmos store support in v0.4.
