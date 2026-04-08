# Development Checklist

## Phase 0: Design Finalization
- [ ] Finalize package name
- [ ] Finalize public API names
- [ ] Finalize semantics documentation
- [ ] Finalize 3 target DBs for MVP

## Phase 1: Core Implementation
- [ ] RowChange
- [ ] PollContext
- [ ] Error hierarchy
- [ ] Retry helper
- [ ] PollRunner

## Phase 2: State Storage
- [ ] BlobCheckpointStore
- [ ] Lease/fencing implementation
- [ ] Checkpoint serializer
- [ ] Source fingerprint

## Phase 3: Adapters
- [ ] SQLAlchemy base adapter
- [ ] Postgres adapter
- [ ] MySQL adapter
- [ ] SQL Server adapter
- [ ] Contract tests

## Phase 4: Functions Integration
- [ ] Imperative runner
- [ ] Decorator sugar
- [ ] Sample function_app.py
- [ ] Local runtime smoke test

## Phase 5: Observability
- [ ] Structured logs
- [ ] Metrics hooks
- [ ] Lag calculation
- [ ] Dashboard examples

## Phase 6: Release
- [ ] README quickstart
- [ ] PyPI metadata
- [ ] Versioning
- [ ] Changelog
- [ ] Release checklist

## Phase 7: Hardening
- [ ] Chaos tests
- [ ] Crash recovery tests
- [ ] Duplicate window documentation
- [ ] Benchmark

## Phase 8: Shared Core
- [ ] DbConfig
- [ ] EngineProvider (lazy singleton, pool management)
- [ ] Shared types (Row, RowDict)
- [ ] Shared error hierarchy refactor
- [ ] Shared serializers extraction

## Phase 9: Binding - Input
- [ ] DbReader
- [ ] get() (single row by PK)
- [ ] query() (raw SQL)
- [ ] Connection lifecycle
- [ ] Unit tests
- [ ] Integration tests (Postgres/MySQL/SQL Server)

## Phase 10: Binding - Output
- [ ] DbWriter
- [ ] insert / upsert / update / delete
- [ ] insert_many / upsert_many (batch)
- [ ] Transaction management
- [ ] Unit tests
- [ ] Integration tests (Postgres/MySQL/SQL Server)

## Phase 11: Binding Integration
- [ ] Trigger + output binding combined example
- [ ] Binding decorator sugar (optional)
- [ ] Docs update
- [ ] Sample function_app.py with binding
