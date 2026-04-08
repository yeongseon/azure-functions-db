# azure-functions-db 문서 패키지

`azure-functions-db`는 **Azure Functions Python 앱 위에서 동작하는 SQLAlchemy 스타일 pseudo DB trigger 프레임워크**를 목표로 하는 프로젝트다.

핵심 아이디어는 단순하다.

- Azure Functions의 **native timer trigger**를 실행 기반으로 사용한다.
- DB 변경 감지는 라이브러리의 **poll / CDC adapter / outbox 전략**이 담당한다.
- 사용자는 이를 `trigger-like` API로 사용한다.
- 여러 RDBMS는 SQLAlchemy dialect/driver 생태계를 최대한 활용한다.
- 운영상 중요한 상태는 checkpoint / lease / dedup 계층이 책임진다.

이 패키지에는 실제 개발에 바로 들어갈 수 있게 다음 문서가 포함되어 있다.

## 문서 인덱스

- `docs/00-프로젝트-개요.md`
- `docs/01-PRD.md`
- `docs/02-아키텍처.md`
- `docs/03-의미론-semantics.md`
- `docs/04-Python-API-스펙.md`
- `docs/05-Adapter-SDK.md`
- `docs/06-Checkpoint-Lease-스펙.md`
- `docs/07-이벤트-모델.md`
- `docs/08-레포-구조.md`
- `docs/09-로컬-개발-가이드.md`
- `docs/10-테스트-전략.md`
- `docs/11-운영-관측성.md`
- `docs/12-보안-설정.md`
- `docs/13-배포-가이드.md`
- `docs/14-로드맵.md`
- `docs/15-CONTRIBUTING.md`
- `docs/16-ADR-001-네이티브-트리거-대신-pseudo-trigger.md`
- `docs/17-ADR-002-SQLAlchemy-중심-adapter.md`
- `docs/18-ADR-003-Blob-checkpoint-MVP.md`
- `docs/19-ADR-004-at-least-once-기본-보장.md`
- `docs/20-오픈-이슈.md`
- `docs/21-개발-체크리스트.md`
- `docs/99-레퍼런스.md`

## 예제 파일

- `examples/function_app.py`
- `examples/usage_postgres.py`
- `examples/host.json`
- `examples/local.settings.sample.json`
- `examples/requirements.txt`
- `examples/pyproject.toml`

## JSON Schema

- `schemas/poller-config.schema.json`
- `schemas/event.schema.json`

## 추천 읽는 순서

1. 프로젝트 개요
2. PRD
3. 아키텍처
4. semantics
5. Python API 스펙
6. Checkpoint/Lease 스펙
7. 테스트/운영/배포 문서

## 한 줄 결론

이 프로젝트는 **진짜 Azure Functions custom trigger**를 DB마다 새로 만드는 것이 아니라,
**Timer + checkpoint + adapter + SQLAlchemy dialect**를 조합해
실무적으로 신뢰할 수 있는 `pseudo trigger experience`를 제공하는 것이 목표다.
