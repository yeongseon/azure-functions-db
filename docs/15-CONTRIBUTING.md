# CONTRIBUTING

## Principles

- PRs that change semantics must include an ADR or design note.
- New adapters may not be merged without contract tests.
- Public API additions must be accompanied by docs and example updates.
- Do not use language that overstates guarantees.

## Branch / PR Rules

- feature/*
- fix/*
- docs/*
- adr/*

Required PR template fields:
- What is being changed
- Why it is needed
- Semantics impact
- Whether migration is required
- Whether tests are added

## Code Style

- Python type hints required
- Public surface docstrings required
- Use structured logging
- No `print` statements (except in examples)
- No direct SQL string concatenation

## Test Rules

- Unit tests first
- Adapters must include integration tests
- Lease/checkpoint changes must include race tests
- Failure/restart tests required

## Documentation Rules

README, PRD, and semantics documents must not contradict each other.
User-facing documentation must always preserve the following statement:

> pseudo trigger / at-least-once / idempotent handler required
