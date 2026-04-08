# Operations / Observability

## 1. Goals

When an issue occurs, operators must be able to answer the following questions:

- Is the poller currently running?
- When was the last successful execution?
- How far behind is it?
- Is the failure caused by the source, handler, or commit?
- Are duplicates increasing?

## 2. Structured Logging

Emit structured logs at every major step.

Required fields:
- poller_name
- invocation_id
- batch_id
- source
- schedule_time
- fetched_count
- committed
- checkpoint_before
- checkpoint_after
- lease_owner
- fencing_token
- duration_ms
- error_type

## 3. Metrics

### Counter
- `azfdb_batches_total`
- `azfdb_events_total`
- `azfdb_failures_total`
- `azfdb_duplicates_total`
- `azfdb_quarantined_total`

### Histogram
- `azfdb_fetch_duration_ms`
- `azfdb_handler_duration_ms`
- `azfdb_commit_duration_ms`
- `azfdb_batch_size`

### Gauge
- `azfdb_lag_seconds`
- `azfdb_last_success_timestamp`
- `azfdb_lease_staleness_seconds`

## 4. Tracing

Where possible, wrap each tick as a single trace/span.

Span structure:
- poll tick
  - lease acquire
  - fetch
  - normalize
  - handler
  - checkpoint commit

## 5. Lag Definition

Lag definition varies by strategy.

### Cursor timestamp-based
```text
lag_seconds = now_utc - last_successful_cursor_timestamp
```

### Integer sequence-based
Use the difference between DB max(version) and the checkpoint.

## 6. Alerts

Minimum alerts:
- No success for 15+ minutes
- 5 consecutive failures
- Sudden lag spike
- Stale lease
- Increasing quarantine count

## 7. Operational Commands

Supported via CLI or management scripts:

- checkpoint inspect
- checkpoint reset
- checkpoint clone
- force lease break (use with caution)
- dry-run fetch
- backfill preview

## 8. Quarantine

If a batch repeatedly fails, the payload can be sent to a quarantine sink.

MVP:
- optional blob sink

Format:
```json
{
  "poller_name": "orders",
  "batch_id": "batch_...",
  "error": "...",
  "events": [...]
}
```

## 9. Operations Dashboard

Recommended cards:
- poller health table
- last success
- lag
- events/min
- failure rate
- top error types

## 10. Runbook Examples

### When a batch keeps failing
1. Inspect checkpoint
2. Dry-run source query
3. Identify the offending row
4. Decide whether to roll back handler code
5. If necessary, send to quarantine — do not manually advance checkpoint

### When lag spikes suddenly
1. Consider increasing batch size
2. Consider increasing max_batches_per_tick
3. Adjust schedule
4. Check for handler downstream bottlenecks
