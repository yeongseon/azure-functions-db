# Python API 스펙

## 1. 디자인 목표

- Azure Functions Python v2와 자연스럽게 맞아야 한다.
- 사용자는 DB polling orchestration보다 handler에 집중해야 한다.
- 단순한 경우는 10줄 내로 끝나야 한다.
- 고급 사용자는 imperative API로 세부 제어 가능해야 한다.

## 2. 표면 API

### 2.1 권장 방식: helper + Azure schedule decorator

```python
import azure.functions as func
from azure_functions_db import PollTrigger, SqlAlchemySource, BlobCheckpointStore

app = func.FunctionApp()

orders_trigger = PollTrigger(
    name="orders",
    source=SqlAlchemySource(
        url="%ORDERS_DB_URL%",
        table="orders",
        schema="public",
        cursor_column="updated_at",
        pk_columns=["id"],
    ),
    checkpoint_store=BlobCheckpointStore(
        connection="AzureWebJobsStorage",
        container="db-state",
    ),
    batch_size=100,
)

@app.function_name(name="orders_poll")
@app.schedule(schedule="0 */1 * * * *", arg_name="timer", use_monitor=True)
def orders_poll(timer: func.TimerRequest) -> None:
    orders_trigger.run(timer=timer, handler=handle_orders)

def handle_orders(events, context):
    for event in events:
        print(event.pk, event.after)
```

### 2.2 decorator sugar

```python
import azure.functions as func
from azure_functions_db import db

app = func.FunctionApp()

@app.function_name(name="orders_poll")
@app.schedule(schedule="0 */1 * * * *", arg_name="timer", use_monitor=True)
@db.poll(
    name="orders",
    url="%ORDERS_DB_URL%",
    table="orders",
    schema="public",
    cursor_column="updated_at",
    pk_columns=["id"],
    checkpoint_store="blob://AzureWebJobsStorage/db-state",
    batch_size=100,
)
def handle_orders(events, context):
    ...
```

실제 구현에서는 decorator가 wrapper를 생성하되, Azure Functions decorator와의 충돌이 없도록
wrapper signature를 단순하게 유지한다.

## 3. 핵심 타입

### 3.1 PollTrigger
```python
class PollTrigger:
    def __init__(
        self,
        *,
        name: str,
        source: SourceAdapter,
        checkpoint_store: CheckpointStore,
        batch_size: int = 100,
        max_batches_per_tick: int = 1,
        lease_ttl_seconds: int = 120,
        heartbeat_interval_seconds: int = 20,
        retry_policy: RetryPolicy | None = None,
        quarantine: QuarantineSink | None = None,
        serializer: EventSerializer | None = None,
    ): ...
```

### 3.2 SqlAlchemySource
```python
class SqlAlchemySource(SourceAdapter):
    def __init__(
        self,
        *,
        url: str,
        table: str | None = None,
        schema: str | None = None,
        query: str | None = None,
        cursor_column: str,
        pk_columns: list[str],
        where: str | None = None,
        parameters: dict[str, object] | None = None,
        strategy: str = "cursor",
        operation_mode: str = "upsert_only",
    ): ...
```

### 3.3 PollContext
```python
@dataclass
class PollContext:
    poller_name: str
    invocation_id: str
    batch_id: str
    lease_owner: str
    checkpoint_before: dict
    checkpoint_after_candidate: dict | None
    tick_started_at: datetime
    source_name: str
```

### 3.4 RowChange
```python
@dataclass
class RowChange:
    event_id: str
    op: str                       # insert | update | upsert | delete | unknown
    source: SourceDescriptor
    cursor: CursorValue
    pk: dict[str, object]
    before: dict[str, object] | None
    after: dict[str, object] | None
    metadata: dict[str, object]
```

## 4. Handler 규칙

지원 signature:

```python
def handler(events): ...
def handler(events, context): ...
async def handler(events): ...
async def handler(events, context): ...
```

규칙:
- `events`는 비어 있을 수도 있다. 기본값은 **empty batch skip**.
- handler가 예외를 던지면 batch 실패로 간주한다.
- handler는 가능하면 idempotent 해야 한다.

## 5. Source 정의 방식

### 5.1 Table mode
- table
- schema
- cursor_column
- pk_columns

### 5.2 Query mode
- query
- cursor_column alias
- pk column alias
- parameterized query

### 5.3 Outbox mode
- table=`outbox_events`
- payload column
- status column optional

## 6. 권장 설정 기본값

- `batch_size=100`
- `max_batches_per_tick=1`
- `lease_ttl_seconds=120`
- `heartbeat_interval_seconds=20`
- `use_monitor=True`
- `schedule=0 */1 * * * *` (1분)

## 7. 에러 분류

```python
class PollerError(Exception): ...
class LeaseAcquireError(PollerError): ...
class SourceConfigurationError(PollerError): ...
class FetchError(PollerError): ...
class HandlerError(PollerError): ...
class CommitError(PollerError): ...
class LostLeaseError(PollerError): ...
class SerializationError(PollerError): ...
```

## 8. 향후 API

- `db.outbox(...)`
- `db.backfill(...)`
- `db.relay(service_bus=...)`
- `db.model(OrderModel)`
- `db.partitioned(...)`

## 9. API 안정성 정책

### Experimental
- CDC strategy
- relay mode
- dynamic partitioning

### Beta
- decorator sugar
- Pydantic mapping

### Stable target
- PollTrigger
- SqlAlchemySource
- BlobCheckpointStore
- RowChange
- PollContext

## 10. Binding API

### 10.1 DbReader (imperative input binding)

```python
from azure_functions_db import DbReader

reader = DbReader(url="%DB_URL%", table="users")
user = reader.get(pk={"id": user_id})  # single row
users = reader.query("SELECT * FROM users WHERE active = :active", params={"active": True})  # query
```

### 10.2 DbWriter (imperative output binding)

```python
from azure_functions_db import DbWriter

writer = DbWriter(url="%DB_URL%", table="processed_orders")
writer.insert(data={"id": 1, "status": "done"})
writer.upsert(data={"id": 1, "status": "done"}, conflict_columns=["id"])
writer.insert_many(rows=[...])
writer.upsert_many(rows=[...], conflict_columns=["id"])
```

### 10.3 Combined trigger + binding example

```python
import azure.functions as func
from azure_functions_db import PollTrigger, SqlAlchemySource, BlobCheckpointStore, DbWriter

app = func.FunctionApp()

orders_trigger = PollTrigger(
    name="orders",
    source=SqlAlchemySource(
        url="%ORDERS_DB_URL%",
        table="orders",
        schema="public",
        cursor_column="updated_at",
        pk_columns=["id"],
    ),
    checkpoint_store=BlobCheckpointStore(
        connection="AzureWebJobsStorage",
        container="db-state",
    ),
)

@app.function_name(name="orders_sync")
@app.schedule(schedule="0 */1 * * * *", arg_name="timer", use_monitor=True)
def orders_sync(timer: func.TimerRequest) -> None:
    orders_trigger.run(timer=timer, handler=handle_orders)

def handle_orders(events, context):
    writer = DbWriter(url="%ANALYTICS_DB_URL%", table="processed_orders")
    try:
        rows = [
            {"id": event.pk["id"], "status": "processed"}
            for event in events
        ]
        if rows:
            writer.upsert_many(rows=rows, conflict_columns=["id"])
    finally:
        writer.close()
```

### 10.4 DbReader types

```python
class DbReader:
    def __init__(self, *, url: str, table: str | None = None, schema: str | None = None): ...
    def get(self, *, pk: dict[str, object]) -> dict[str, object] | None: ...
    def query(self, sql: str, *, params: dict[str, object] | None = None) -> list[dict[str, object]]: ...
    def close(self) -> None: ...
```

### 10.5 DbWriter types

```python
class DbWriter:
    def __init__(self, *, url: str, table: str, schema: str | None = None): ...
    def insert(self, *, data: dict[str, object]) -> None: ...
    def upsert(self, *, data: dict[str, object], conflict_columns: list[str]) -> None: ...
    def update(self, *, data: dict[str, object], pk: dict[str, object]) -> None: ...
    def delete(self, *, pk: dict[str, object]) -> None: ...
    def insert_many(self, *, rows: list[dict[str, object]]) -> None: ...
    def upsert_many(self, *, rows: list[dict[str, object]], conflict_columns: list[str]) -> None: ...
    def close(self) -> None: ...
```

### 10.6 Binding error classes

```python
class DbError(Exception): ...
class ConnectionError(DbError): ...
class QueryError(DbError): ...
class WriteError(DbError): ...
class NotFoundError(DbError): ...
```

## 11. Shared Core API

### 11.1 DbConfig

```python
@dataclass(frozen=True)
class DbConfig:
    url: str
    table: str | None = None
    schema: str | None = None
```

### 11.2 EngineProvider (shared engine/pool management, lazy singleton per config)

```python
class EngineProvider:
    @classmethod
    def get_or_create(cls, config: DbConfig): ...

    @classmethod
    def dispose(cls, config: DbConfig) -> None: ...
```
