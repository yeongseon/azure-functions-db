# Deployment Guide

## 1. Recommended Deployment Model

### MVP
- Azure Functions Python app
- Azure Storage account
- Target DB
- Application Insights

## 2. Environment Separation

- dev
- staging
- prod

Separate per environment:
- function app
- storage account/container namespace
- checkpoint path
- DB endpoint
- app insights

## 3. Recommended host.json

```json
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.0.0, 5.0.0)"
  },
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true
      }
    }
  }
}
```

## 4. App Settings

Required:
- `AzureWebJobsStorage`
- `FUNCTIONS_WORKER_RUNTIME=python`
- `ORDERS_DB_URL`
- `AZFDB_STATE_CONTAINER=db-state`

Optional:
- `DBTRIGGER_LOG_LEVEL=INFO`
- `DBTRIGGER_MAX_BATCHES_PER_TICK=1`
- `DBTRIGGER_DEFAULT_BATCH_SIZE=100`

## 5. Rollout Procedure

1. Deploy to staging
2. Local + staging smoke test
3. Create new checkpoint namespace
4. Activate 1 canary poller
5. Observe lag / duplicate / failure rate
6. Activate full prod

## 6. Upgrade Principles

The following changes are risky:
- Source query changes
- Cursor column changes
- PK changes
- Checkpoint schema changes

Principles:
- Do not reuse the same checkpoint if the source fingerprint changes
- If required, plan a migration or reset

## 7. Deployment Checklist

- [ ] Confirm extension bundle 4.x
- [ ] Confirm DB connection reachability
- [ ] Confirm storage permissions
- [ ] Confirm no schedule conflicts
- [ ] Review function timeout
- [ ] Confirm Application Insights connectivity
- [ ] Create alert rules

## 8. Disaster Recovery

### Transient Storage Failure
- Bounded retry
- Function fails on extended outage
- Checkpoint remains unadvanced

### Extended DB Failure
- Allow lag to accumulate
- Catch-up after recovery
- Schedule/batch size can be re-adjusted

### Bad Deployment
- Rollback
- Checkpoint is generally preserved
- If source contract has changed, verify fingerprint even after rollback
