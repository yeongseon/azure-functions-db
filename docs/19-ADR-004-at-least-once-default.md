# ADR-004: Define Default Guarantee as At-Least-Once

## Status
Accepted

## Context

In a pseudo trigger environment, exactly-once delivery introduces excessive complexity.
Conversely, ensuring no events are missed is more important than preventing duplicates.

## Decision

The default contract is defined as **delivery that approximates at-least-once**.

## Rationale

- Fits naturally with the batch-success-then-commit model
- On crash or commit failure, allowing duplicates is safer than risking loss
- The requirement for an idempotent handler can be communicated clearly to users

## Consequences
- Handlers and downstream consumers must be designed to tolerate duplicates
- Documentation must prevent misunderstanding of exactly-once semantics
- A dedup helper is provided as an optional feature
