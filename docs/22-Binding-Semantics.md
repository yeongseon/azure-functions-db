# Binding Semantics

## 1. 목적
binding은 Azure Functions 함수에서 DB 데이터를 읽고 쓰는 imperative helper다.
trigger와 달리 상태(checkpoint/lease)를 관리하지 않으며, 함수 호출 단위로 동작한다.

## 2. 제품 경계
- 이 라이브러리는 Python 레벨의 DB helper다
- Azure Functions host-native binding extension이 아니다
- 사용자는 함수 본문에서 DbReader/DbWriter를 직접 호출한다

## 3. Input Binding (DbReader)

### 3.1 기본 계약
- 호출 단위 read (invocation-scoped)
- DB 기본 isolation level 사용 (별도 지정 가능)
- 여러 read 간 snapshot/repeatable-read 보장 없음
- None = "row not found" (DB 접근 실패가 아님)

### 3.2 실패 의미
- DB 연결 실패 → ConnectionError raise (함수 실패)
- 쿼리 실패 → QueryError raise (함수 실패)
- row 없음 → None 반환 (정상 동작)
- fail closed 원칙: 운영 장애를 None/빈 리스트로 숨기지 않는다

### 3.3 Connection lifecycle
- DbReader 생성 시 EngineProvider에서 engine 획득 (lazy singleton)
- 각 get()/query() 호출마다 짧은 connection 사용
- 장기 session 유지하지 않음
- close() 호출 시 reader 자원 해제 (engine pool은 유지)

## 4. Output Binding (DbWriter)

### 4.1 기본 계약
- 호출 단위 write (invocation-scoped)
- 각 write 호출(insert/upsert/update/delete)이 독립 transaction
- batch 메서드(insert_many/upsert_many)는 all-or-nothing

### 4.2 Transaction 경계
- 기본: 호출 단위 autocommit
- batch: 단일 transaction으로 감싸서 all-or-nothing
- 여러 write 호출 간 transaction 보장 없음 (각각 독립)
- 향후 필요 시 DbSession context manager로 명시적 multi-write transaction 제공

### 4.3 실패 의미
- DB 연결 실패 → ConnectionError raise
- write 실패 (constraint violation 등) → WriteError raise
- batch 중 실패 → 전체 batch rollback, WriteError raise
- 함수 실패 처리: Azure Functions retry policy에 위임 (라이브러리 내부 retry 없음)

### 4.4 Idempotency
- upsert는 본질적으로 idempotent
- insert는 PK 충돌 시 WriteError
- 사용자가 retry 안전을 원하면 upsert 사용 권장

### 4.5 Connection lifecycle
- DbWriter 생성 시 EngineProvider에서 engine 획득 (lazy singleton)
- 각 write 호출마다 짧은 connection + transaction
- close() 호출 시 writer 자원 해제

## 5. Trigger + Binding 조합

### 5.1 독립성
- trigger의 checkpoint/lease와 binding의 write는 별도 transaction
- trigger handler 내에서 DbWriter 사용 가능하지만, checkpoint commit과 무관
- output write 성공 ≠ checkpoint 전진

### 5.2 실패 시나리오
- handler 내 DbWriter.insert() 성공 → handler 성공 → checkpoint commit 실패
  → 다음 tick에서 같은 batch 재처리 → DbWriter.insert() 중복 실행 가능
  → 사용자는 upsert 사용 또는 idempotent key 필요

### 5.3 Engine 공유
- trigger와 binding이 같은 DB URL을 사용하면 EngineProvider가 동일 engine 반환
- connection pool 공유, session/transaction은 독립

## 6. Shared Core 규약

### 6.1 EngineProvider
- DbConfig를 key로 lazy singleton engine 관리
- 같은 config = 같은 engine/pool
- thread-safe

### 6.2 DbConfig
- url (필수)
- pool_size, max_overflow, pool_timeout (선택)
- connect_args (선택)
- echo (선택, 디버깅용)

### 6.3 Error hierarchy
- DbError (base)
  - ConnectionError
  - QueryError
  - WriteError
  - NotFoundError
- trigger 전용: PollerError hierarchy (기존 유지, DbError와 독립)

## 7. 향후 확장

### 7.1 Decorator sugar (Phase 11+)
- @db.input(), @db.output() — thin wrapper over DbReader/DbWriter
- imperative API가 안정화된 후에만 추가

### 7.2 DbSession (필요 시)
- 명시적 multi-write transaction context manager
- ambient transaction 없음
- 사용자가 명시적으로 opt-in

### 7.3 Pydantic mapping
- DbReader.get() → Pydantic model 반환 옵션
- DbWriter.insert() → Pydantic model 입력 옵션

## 8. 사용자에게 반드시 알릴 문구

> azure-functions-db의 binding은 Azure Functions host-native binding이 아니라,
> 함수 본문에서 호출하는 Python 레벨 DB helper다.
> write는 호출 단위 transaction이며, trigger의 checkpoint commit과 독립적이다.
