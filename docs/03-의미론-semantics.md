# 의미론 (Semantics)

이 문서는 프로젝트의 **가장 중요한 계약**을 정의한다.

## 1. 기본 보장

### 1.1 Delivery Contract (정밀 정의)
기본 보장 수준은 **at-least-once**다.

정밀 정의:
> source에서 checkpoint `C` 이후에 adapter query에 보이는 변경은,
> 해당 batch의 checkpoint commit이 성공할 때까지 0회 이상 handler에 전달될 수 있다.
> checkpoint commit이 성공하면, 프레임워크는 그 checkpoint 이하의 row를 의도적으로 다시 읽지 않는다.
> 단, 이는 아래 source 전제조건이 충족될 때에만 유효하다.

### 1.2 Source 전제조건
프레임워크가 올바르게 동작하기 위해 source가 만족해야 하는 조건:
- cursor column은 **단조 증가(monotonic non-decreasing)**여야 한다
- PK/tiebreaker는 **안정적이고 전순서(total order)**가 가능해야 한다
- source query는 **결정적(deterministic)**이어야 한다
- cursor 정밀도가 너무 낮으면 중간 update가 하나로 합쳐질 수 있다

### 1.3 인정(Acknowledgment) 경계
- **handler 성공 ≠ 인정**. handler가 성공해도 checkpoint commit이 실패하면 batch는 미인정 상태다.
- **checkpoint commit 성공 = 인정**. 이 시점에서만 batch가 확정된다.
- commit 응답이 모호(타임아웃)한 경우, 다음 tick에서 state 재로드로 판별한다.

### 1.4 Exactly-once 아님
다음을 보장하지 않는다.

- 전역 exactly-once
- cross-instance 완전 무중복
- cross-DB transactional exactly-once

### 1.5 Ordering
기본 ordering은 다음 범위에서만 시도한다.

- 같은 poller 내
- 같은 source query 내
- `ORDER BY cursor ASC, pk ASC`

전역 ordering은 보장하지 않는다.

## 2. Checkpoint 의미

checkpoint는 "이 시점까지 **성공적으로 처리 완료된 마지막 event**"를 뜻한다.

기본적으로 다음 형식이다.

```text
(cursor_value, tiebreaker_pk, batch_id)
```

### 중요
checkpoint는 fetch 직후가 아니라 **handler 성공 후** 전진한다.

## 3. Duplicate 허용 정책

다음 상황에서 중복이 발생할 수 있다.

- handler 성공 직후 checkpoint commit 전 프로세스 종료
- lease 만료 후 다른 인스턴스 재처리
- timer overlap
- DB isolation 특성으로 인한 재조회
- 재배포/재시작

따라서 사용자 handler는 기본적으로 idempotent 해야 한다.

권장 패턴:
- event_id 기반 dedup
- target side upsert
- processed table 기록
- downstream idempotency key 사용

## 4. Delete 의미

cursor polling 전략에서 hard delete는 기본적으로 감지되지 않는다.

지원 방식:
- soft delete column (`deleted_at`, `is_deleted`)
- outbox row 기록
- native CDC strategy
- tombstone table

문서/코드에서 delete를 지원한다고 적으려면 **전략별로 분리**해서 명시한다.

## 5. Cursor 의미

### 지원 cursor 유형
- monotonic integer/bigint
- timestamp/datetime
- logical version column
- composite cursor

### 권장 cursor
- `updated_at` + stable PK
- `version` + stable PK

### 비권장 cursor
- 정렬 불안정한 문자열
- timezone 불명확한 naive datetime
- 업데이트 안 되는 created_at 단일값

## 6. Timestamp tie 처리

같은 timestamp를 가진 여러 row가 한 batch에 걸쳐 나뉠 수 있다.
따라서 checkpoint는 단일 timestamp가 아니라 **timestamp + PK tiebreaker**를 사용한다.

정렬 규칙:
1. cursor ASC
2. PK ASC (복합 PK면 tuple ASC)

## 7. Batch 의미

한 번 handler에 전달되는 event 집합을 batch라 한다.

기본 정책:
- batch size 고정 상한 있음
- batch 전체 성공 시 checkpoint advance
- batch 일부 실패 시 전체 batch 재처리

### 향후 옵션
- row-by-row commit
- partial batch ack
- quarantine split

MVP에는 포함하지 않는다.

## 8. Retry 의미

Functions 런타임 retry와 라이브러리 내부 retry를 혼동하면 안 된다.

원칙:
- DB fetch/retriable infra error: 라이브러리 내부 bounded retry 가능
- handler business error: 함수 실패로 surface
- checkpoint commit error: commit 실패면 batch는 미확정 상태로 남음

## 9. Lease 의미

lease는 "현재 poller 실행의 write authority"다.

규칙:
- 유효 lease 없이 checkpoint commit 금지
- fencing token 낮으면 commit 거부
- lease 만료 전 heartbeat 필요

## 10. Visibility delay

pseudo trigger는 real-time push trigger가 아니다.
지연은 대략 다음에 의해 결정된다.

```text
visibility_delay ~= schedule_interval + query_time + handler_time + commit_time
```

사용자는 이 값을 이해하고 schedule을 잡아야 한다.

## 11. Backfill mode

backfill은 운영 모드와 의미가 다르다.

- 대량 historical replay
- 고빈도 trigger-like 반응성보다 throughput 우선
- 일반 운영 checkpoint와 분리 가능해야 함

권장:
- 별도 poller name 사용
- 별도 checkpoint namespace 사용

## 12. Failure matrix

### 사례 A: handler 실패
- checkpoint 전진 안 함
- 다음 tick에 재처리 가능

### 사례 B: handler 성공, commit 실패
- batch 재처리 가능
- duplicate 발생 가능
- handler 성공은 인정(acknowledgment)이 아님

### 사례 C: lease 상실 후 commit 시도
- CAS etag 불일치로 commit 자동 거부
- duplicate 가능 (다른 인스턴스가 같은 batch 재처리)
- loss 방지 우선

### 사례 D: DB row가 update 후 다시 update
- 최신 상태만 보일 수 있음
- old/new diff는 전략에 따라 다름

### 사례 E: fetch 후 handler 시작 전 crash
- checkpoint 변경 없음
- 다음 tick에 같은 batch 재처리
- duplicate 가능, loss 없음

### 사례 F: handler 중 부분 side effect 후 crash
- checkpoint 변경 없음
- 전체 batch 재처리
- handler는 반드시 idempotent 해야 함

### 사례 G: commit 응답 타임아웃 (모호한 상태)
- commit 성공 여부 불확실
- 다음 tick에서 state 재로드로 판별
- 최악의 경우 duplicate, loss 없음

### 사례 H: heartbeat 실패로 lease 상실
- handler 진행 중이라도 lease 이미 만료
- commit 시도 시 CAS 실패
- handler 결과 버려짐, 다음 owner가 재처리

### 사례 I: 영구 실패 batch (poison message)
- 동일 batch가 무한 재시도될 수 있음
- quarantine sink로 분리하거나 수동 checkpoint advance 필요
- MVP에서는 운영자 개입 필요

## 13. 사용자에게 반드시 알릴 문구

README / docs / docstring에 반드시 유지:

> azure-functions-db는 native database trigger가 아니라,
> Azure Functions timer 기반의 pseudo trigger 프레임워크다.
> 기본 보장은 at-least-once에 가깝고, handler는 idempotent 해야 한다.
