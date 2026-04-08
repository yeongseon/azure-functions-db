# Local Development Guide

## 1. Development Environment

Recommended:
- Python 3.11+
- Azure Functions Core Tools 4.x
- Docker (for DB integration tests)
- Azurite or an actual dev storage account as an alternative to Azure Storage Emulator
- uv or pip + venv

## 2. Creating an Azure Functions Python v2 App

```bash
func init myfuncapp --python
cd myfuncapp
func new --name orders_poll --template "Timer trigger"
```

Afterwards, organize the project around `function_app.py` following the Python v2 structure.

## 3. Installing Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r examples/requirements.txt
```

## 4. Checking host.json

Keep the extension bundle 4.x range in `host.json`.

```json
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.0.0, 5.0.0)"
  }
}
```

## 5. local.settings.json

Example:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ORDERS_DB_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/orders"
  }
}
```

## 6. Running Locally

```bash
func start
```

## 7. Recommended Local Test Sequence

1. Pure unit tests
2. SQLite smoke test
3. Docker Postgres integration test
4. Docker MySQL integration test
5. Docker SQL Server integration test
6. Local Functions runtime smoke test

## 8. Sample DB for Development

### PostgreSQL
- table: orders
- cursor: updated_at
- pk: id

### Seed Example
```sql
CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  status TEXT NOT NULL,
  total_amount NUMERIC(12,2) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO orders (status, total_amount) VALUES
('created', 10.50),
('paid', 20.00);
```

## 9. Local Debugging Checkpoints

- checkpoint JSON contents
- generated SQL
- fetched batch size
- lease owner / fencing token
- handler execution time
- commit success status

## 10. Caveats

- `updated_at` must be reliably updated by the application.
- Do not mix local clock and DB timezone.
- An empty batch is a success case.
- Hard deletes are not captured by default polling.
