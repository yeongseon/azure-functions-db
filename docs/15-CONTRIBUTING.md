# CONTRIBUTING

## 원칙

- semantics를 바꾸는 PR은 반드시 ADR 또는 design note 포함
- 새 adapter는 contract test 없으면 merge 금지
- public API 추가 시 docs/예제 같이 수정
- guarantee를 과장하는 문구 금지

## 브랜치/PR 규칙

- feature/* 
- fix/*
- docs/*
- adr/*

PR 템플릿 필수 항목:
- 무엇을 바꾸는가
- 왜 필요한가
- semantics 영향
- migration 필요 여부
- 테스트 추가 여부

## 코드 스타일

- Python type hints 필수
- public surface docstring 필수
- structured logging 사용
- `print` 금지(예제 제외)
- SQL string format 직접 연결 금지

## 테스트 규칙

- unit test 먼저
- adapter는 integration test 포함
- lease/checkpoint 수정 시 race test 포함
- failure/restart test 필수

## 문서 규칙

README/PRD/semantics 중 하나라도 모순되면 안 된다.
사용자-facing 문서에서 반드시 다음 내용을 유지한다.

> pseudo trigger / at-least-once / idempotent handler required
