# Adapter SDK

이 문서는 DB adapter를 추가하는 개발자를 위한 내부/외부 확장 규약이다.

## 1. 목적

새 DB를 지원할 때 애플리케이션 레벨 코드나 PollRunner를 수정하지 않고,
adapter만 추가해서 연결할 수 있어야 한다.

## 2. Adapter 분류

### 2.1 SQLAlchemyAdapter
RDBMS 공통 기반 adapter.
- PostgreSQL
- MySQL/MariaDB
- SQL Server
- Oracle
- SQLite

### 2.2 NativeAdapter
SQLAlchemy로 다루기 어려운 DB 또는 native change stream 제공 DB.
- MongoDB
- Kafka-backed source
- custom REST cursor source

## 3. Base Protocol

```python
class SourceAdapter(Protocol):
    name: str

    def validate(self) -> None: ...
    def open(self) -> None: ...
    def close(self) -> None: ...
    def fetch_changes(self, checkpoint: Checkpoint, limit: int) -> FetchResult: ...
    def capability(self) -> AdapterCapability: ...
    def source_descriptor(self) -> SourceDescriptor: ...
```

adapter는 raw record를 반환하고, core가 RowChange로 정규화한다.
`supports_deletes()`는 `capability()` 안에 통합되었다.

## 4. FetchResult

```python
@dataclass
class RawRecord:
    """adapter가 반환하는 정규화 전 레코드"""
    row: dict[str, object]        # DB에서 읽은 raw row
    cursor_value: object           # cursor column 값
    pk_values: dict[str, object]   # PK dict

@dataclass
class FetchResult:
    records: list[RawRecord]
    next_checkpoint: Checkpoint | None
    stats: dict[str, object]
```

규칙:
- `records`가 비어 있으면 `next_checkpoint`도 일반적으로 `None`
- `next_checkpoint`는 반드시 마지막 record를 가리켜야 함
- source adapter는 ordering을 안정적으로 유지해야 함
- adapter는 `RowChange`를 생성하지 않음 — core의 EventNormalizer가 담당

## 5. SQLAlchemy adapter 상세

### 필수 입력
- url
- table 또는 query
- cursor_column
- pk_columns

### 필수 책임
- dialect별 quoting 처리
- stable ORDER BY 생성
- parameter binding
- row -> dict 변환
- datetime normalization(UTC 권장)

### 권장 구현
- SQLAlchemy Core 사용
- ORM 세션 의존 최소화
- reflection은 startup에서 1회 캐시 가능

## 6. Query builder 규칙

### Table mode 생성 규칙
```sql
SELECT <projected_columns>
FROM <schema.table>
WHERE (
  cursor > :cursor_value
  OR (cursor = :cursor_value AND pk > :pk_value)
)
ORDER BY cursor ASC, pk ASC
LIMIT :limit
```

복합 PK는 tuple compare 또는 OR-expanded predicate를 사용한다.

### Query mode 규칙
사용자 query를 subquery로 감싼다.

```sql
SELECT *
FROM (
  <user_query>
) AS source
WHERE ...
ORDER BY ...
LIMIT ...
```

## 7. Delete 지원 정책

adapter는 capability로 delete 지원 여부를 명시한다.

```python
@dataclass
class AdapterCapability:
    supports_delete_detection: bool
    supports_before_image: bool
    supports_native_resume_token: bool
    supports_partitioning: bool
```

## 8. Adapter 작성 체크리스트

- [ ] 안정적인 ordering 제공
- [ ] empty result 처리
- [ ] timezone normalization
- [ ] string/integer PK 모두 검증
- [ ] duplicate-safe checkpoint 생성
- [ ] SQL injection-safe parameterization
- [ ] schema reflection fallback
- [ ] integration test 3종 이상

## 9. DB별 메모

### PostgreSQL
- 권장 driver: `psycopg`
- timestamp with time zone 권장
- outbox 전략과 궁합 좋음

### MySQL / MariaDB
- `updated_at` 정밀도 주의
- transaction isolation에 따라 재조회 가능성 고려

### SQL Server
- `rowversion` 또는 datetime2 활용 가능
- official Azure SQL trigger가 change tracking + polling loop를 사용한다는 점을 참고해
  pseudo trigger 문서 모델을 정직하게 유지한다.

### SQLite
- 개발/테스트용 우선
- 운영 pseudo trigger source로는 권장도 낮음

## 10. Non-SQL adapter 지침

MongoDB 같은 adapter는 SQLAlchemy 의존 없이 별도 패키지로 둔다.

예:
- `azure-functions-db-mongo`
- `azure-functions-db-postgres-cdc`

핵심은 공통 `RowChange` contract만 유지하면 된다.
