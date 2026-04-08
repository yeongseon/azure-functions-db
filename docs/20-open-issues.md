# Open Issues

## 1. Delete Detection UX
- Whether to treat soft delete as a first-class citizen
- Whether to provide a tombstone helper

## 2. Cursor Drift
- If the application does not update `updated_at`, events may be missed
- How aggressively to enforce this via lint/validation

## 3. Long-Running Handlers
- How to align Functions timeout with lease heartbeat
- Whether a chunked handler mode is needed

## 4. Source Query Flexibility
- How much latitude to give users for raw queries
- How to surface warnings for unsupported SQL syntax

## 5. Reset UX
- Preventing misuse of the reset command from the CLI
- Whether a dry-run / confirm prompt is needed

## 6. Outbox Helper
- Whether to provide only a simple library
- Whether to also supply a table DDL template

## 7. Driver Extras Policy
- psycopg vs asyncpg
- pymysql vs mysqlclient
- pyodbc vs mssqlpython

## 8. OpenTelemetry
- Whether to include as a core dependency or an extra
