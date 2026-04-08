# PRD

## 1. 제품명
azure-functions-db

## 2. 한 줄 설명
Azure Functions Python 앱에서 DB의 변경 감지(trigger), 읽기(input binding), 쓰기(output binding)를 통합 제공하는 프레임워크.

## 3. 배경

실무에서는 다음 두 요구가 자주 같이 나온다.

- Azure Functions의 serverless execution model을 활용하고 싶다.
- 하지만 데이터 원천은 Azure 고유 서비스가 아니라 다양한 SQL DB다.

이 간극 때문에 각 팀은 다음을 직접 구현한다.

- schedule 실행
- incremental fetch
- watermark 저장
- retry / quarantine
- idempotency
- observability
- DB row 조회용 연결/세션 관리
- 함수 출력 결과를 다른 DB에 기록하는 boilerplate

이 프로젝트는 그 반복 구현을 표준화한다.

## 4. 목표

### 반드시 달성
- Azure Functions Python v2에서 쉽게 붙일 수 있어야 한다.
- Postgres/MySQL/SQL Server에서 최소한 `updated_at` 또는 monotonic cursor 기반으로 동작해야 한다.
- lease/checkpoint/dedup contract가 문서화되어 있어야 한다.
- 실패 시 재실행해도 안전한 패턴을 기본값으로 제공해야 한다.
- handler 개발자가 비즈니스 로직에 집중할 수 있어야 한다.

### 가능하면 달성
- Pydantic model mapping
- OpenTelemetry hook
- backfill mode
- poison batch quarantine
- Event Hub / Service Bus relay mode

## 5. 비목표
- DB 내부 trigger 자체를 생성/관리하는 제품이 아니다.
- Azure Functions host를 확장하는 .NET extension이 아니다.
- SQLAlchemy ORM 대체재가 아니다.
- CDC 플랫폼 전체를 대체하지 않는다.

## 6. 사용자

### 1차 사용자
- Python 기반 Azure Functions 개발자
- 데이터 동기화/후처리/알림 함수를 만드는 백엔드 엔지니어
- DB event-driven workflow를 원하는 팀

### 2차 사용자
- 플랫폼 팀
- 내부 표준 라이브러리 유지보수 팀
- 멀티DB 운영 환경을 가진 팀

## 7. 대표 유스케이스

### UC-1 주문 테이블 변경 후 후처리
orders 테이블의 insert/update를 감지해 ERP, Slack, CRM으로 동기화.

### UC-2 멀티 DB 정기 동기화
여러 고객 DB를 일정 간격으로 훑어 변경분만 처리.

### UC-3 low-cost pseudo CDC
정식 CDC 파이프라인이 과한 서비스에서 간단한 변경 처리 자동화.

### UC-4 outbox 소비
서비스 DB의 outbox 테이블을 안전하게 소비해 Service Bus로 내보냄.

### UC-5 HTTP trigger에서 DB row 조회
HTTP trigger 함수가 `DbReader`를 사용해 요청 파라미터 기준 단건/목록 row를 조회.

### UC-6 함수 결과를 다른 DB 테이블에 기록
함수 실행 결과를 `DbWriter`로 다른 테이블에 insert/upsert하여 후처리 상태를 저장.

### UC-7 trigger로 감지한 변경을 다른 DB에 동기화
trigger가 읽은 변경 이벤트를 handler에서 가공한 뒤 output binding으로 다른 DB에 반영.

## 8. 제품 요구사항

### API 요구사항
- decorator 기반 선언 지원
- imperative runner 지원
- SQLAlchemy URL 사용 가능
- source/table/query 기반 정의 가능
- cursor column, PK, batch size, schedule, retry 정책 지정 가능
- checkpoint store pluggable
- handler pre/post hook 지원

### Binding API 요구사항
- `DbReader`와 `DbWriter`를 public API로 제공해야 함
- `DbReader.get(pk=...)`로 단건 조회 가능해야 함
- `DbReader.query(sql, params=...)`로 raw SQL 조회 가능해야 함
- `DbWriter.insert/upsert/update/delete`를 제공해야 함
- `DbWriter.insert_many/upsert_many`로 batch write 가능해야 함
- trigger handler 내부와 일반 함수 코드 양쪽에서 동일한 방식으로 사용 가능해야 함
- import 이름은 `azure_functions_db`로 일관되어야 함

### 운영 요구사항
- lease 없이 동시에 두 인스턴스가 같은 batch를 처리하지 않도록 해야 함
- batch 성공 전 checkpoint 전진 금지
- 처리 실패 batch를 재시도 가능해야 함
- structured logging 필수
- metrics/export hook 제공

### Binding 운영 요구사항
- 연결/엔진 관리는 shared core를 통해 재사용되어야 함
- binding 실패는 invocation failure로 surface되어야 함(fail closed)
- not found는 예외가 아니라 `None` 반환으로 표현해야 함
- 기본 쓰기 단위는 write call 단위 transaction이어야 함
- ambient transaction 없이도 예측 가능한 동작을 제공해야 함
- Postgres/MySQL/SQL Server에서 동일한 최소 동작 계약을 유지해야 함

### 문서 요구사항
- guarantee 범위를 과장하지 않는다
- delete 감지 한계를 명시한다
- 같은 timestamp 동률 처리 방식 명시
- backfill/normal mode 차이 명시

## 9. 성공 지표

### 초기 정성 지표
- 사용자가 30분 내 local PoC를 띄울 수 있음
- handler 코드가 20줄 미만으로 구현 가능
- DB별 custom polling code 삭제

### 초기 정량 지표
- MVP 3개 DB integration test green
- 1만 row catch-up benchmark에서 누락 0
- 강제 재시작/중복 실행 chaos test에서 duplicate는 허용하되 loss는 0
- README quickstart 완료 시간 20분 이내

## 10. 릴리스 기준

### v0.1 GA-ish 기준
- Postgres/MySQL/SQL Server polling 성공
- Blob checkpoint store 안정화
- at-least-once contract 문서화
- local/CI/integration 예제 제공
- 범위는 trigger 기능으로 한정

### v0.2
- DbReader / DbWriter 추가
- input/output binding 문서화
- Pydantic mapping
- quarantine
- backfill mode
- observability 강화

### v0.3
- Mongo adapter
- outbox helper
- relay mode(Event Hub/Service Bus)

### v0.5
- CDC-capable adapters
- richer partitioning
- dynamic multi-source scheduler
