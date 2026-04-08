# Checkpoint / Lease 스펙

## 1. 목적

pseudo trigger에서 가장 중요한 상태는 checkpoint와 lease다.

- checkpoint: 어디까지 성공적으로 처리했는가
- lease: 지금 누가 처리 권한을 갖는가

**핵심 설계 결정**: checkpoint와 lease를 **단일 state blob**에 저장하고,
모든 상태 변경을 **ETag 기반 CAS(conditional write)**로 수행한다.
이를 통해 별도 blob 간 TOCTOU race condition을 원천 차단한다.

## 2. 저장소 선택

### MVP
- Azure Blob Storage

이유:
- Azure Functions와 같이 쓰기 쉬움
- 운영팀이 이미 갖고 있는 경우가 많음
- 비용/단순성 균형이 좋음
- ETag 기반 conditional write(If-Match) 지원

### 후속 후보
- Azure Table Storage
- Cosmos DB
- SQL table

## 3. Blob 레이아웃

컨테이너: `db-state`

blob path 예시:
```text
state/{app_name}/{poller_name}.json
```

기존의 `checkpoints/` + `leases/` 분리 구조 대신, **단일 state blob**을 사용한다.

## 4. State 문서 형식 (통합)

```json
{
  "version": 1,
  "poller_name": "orders",
  "source_fingerprint": "sha256:...",

  "checkpoint": {
    "cursor": {
      "kind": "timestamp+pk",
      "value": "2026-04-07T01:23:45.123456Z",
      "tiebreaker": {
        "id": 12093
      }
    },
    "last_successful_batch_id": "batch_20260407_012346_0001",
    "updated_at": "2026-04-07T01:23:46.020000Z",
    "metadata": {
      "row_count": 100
    }
  },

  "lease": {
    "owner_id": "funcapp/instance-abc123",
    "fencing_token": 42,
    "acquired_at": "2026-04-07T01:23:00Z",
    "heartbeat_at": "2026-04-07T01:23:20Z",
    "expires_at": "2026-04-07T01:25:00Z"
  }
}
```

## 5. CAS 기반 상태 전이

모든 상태 변경은 다음 패턴을 따른다:

```text
1. state blob 읽기 → (content, etag) 획득
2. 변경 사항 적용 (lease 획득, checkpoint advance 등)
3. conditional write (If-Match: etag)
4. 성공 → 완료
5. 실패 (412 Precondition Failed) → 재시도 또는 포기
```

이 패턴은 lease 획득, heartbeat, checkpoint commit 모두에 동일하게 적용된다.

## 6. Lease 획득 알고리즘

```text
1. state blob 읽기 → (state, etag)
2. state가 없으면 → 새 state 생성 (fencing_token=1)
3. lease가 만료되었으면 → fencing_token++ 후 owner 설정
4. conditional write (If-Match: etag)
5. 성공 → lease 획득 확정
6. 실패 → 다른 인스턴스가 먼저 획득, skip
```

### 규칙
- 만료 전 타 인스턴스 steal 금지
- local clock skew에 대비해 safety margin 사용
- 모든 lease 변경은 CAS로 원자적 수행

## 7. Heartbeat

handler가 오래 걸릴 수 있으므로 heartbeat가 필요하다.

기본 규칙:
- `heartbeat_interval < lease_ttl / 2`
- heartbeat 실패 n회 누적 시 실행 중단 고려
- heartbeat = state blob CAS write (heartbeat_at, expires_at 갱신)
- CAS 실패 = lease 상실, handler 중단 필요

## 8. Commit 알고리즘

```text
1. state blob 읽기 → (state, etag)
2. owner_id / fencing_token 일치 확인
3. checkpoint 갱신 (cursor, batch_id, updated_at)
4. conditional write (If-Match: etag)
5. 성공 → checkpoint 전진 완료
6. 실패 → CommitError (batch는 미확정, 재처리 가능)
```

### 핵심 원칙
- checkpoint와 lease 검증이 **같은 CAS write**에서 이루어짐
- stale owner의 commit은 etag 불일치로 자동 거부됨
- 별도 lease blob 확인 불필요 → TOCTOU race 없음

## 9. Source fingerprint

state에는 source definition hash를 기록한다.

예:
- DB URL(비밀번호 제외)
- table/query
- cursor column
- PK columns
- filters

source fingerprint가 바뀌면 기본 정책:
- 실행 거부 또는
- 명시적 reset/backfill 필요

## 10. Reset 정책

지원 명령:
- `reset_to_beginning`
- `reset_to_checkpoint(file)`
- `reset_to_cursor(value, pk)`
- `clone_checkpoint(new_poller_name)`

운영에서 reset은 위험하므로 CLI에 guardrail 필요.

## 11. 장애 시나리오

### CAS write 성공 후 함수 종료
- 이미 commit됨
- 다음 tick은 이후부터 시작

### handler 성공, CAS write 실패
- 다음 tick에 같은 batch 재처리 가능
- duplicate 발생 가능

### CAS write 응답 타임아웃 (모호한 상태)
- commit 성공 여부 불확실
- 다음 tick에서 state 재로드하여 판별
- 최악의 경우 duplicate 발생, loss는 없음

### lease 만료 후 다른 인스턴스 takeover
- stale owner의 commit 시도는 etag 불일치로 자동 거부
- duplicate 가능, loss 방지

### heartbeat CAS 실패
- lease 상실로 간주
- handler 중단 후 commit 시도하지 않음

## 12. 운영 가이드라인

- 운영 poller당 state blob 1개
- backfill은 별도 poller_name 사용 (별도 state blob)
- source definition 변경 시 state blob 재사용 금지
- storage RBAC 또는 connection string 권한 최소화
