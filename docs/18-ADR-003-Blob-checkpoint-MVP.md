# ADR-003: MVP checkpoint store로 Blob 사용

## 상태
Accepted

## 문맥

checkpoint/lease 저장소는 Azure 환경에서 구하기 쉽고 운영 난도가 낮아야 한다.

## 결정

MVP의 기본 checkpoint/lease 저장소는 Azure Blob Storage로 한다.

## 이유

- Azure Functions와 궁합이 좋음
- 대부분 환경에 이미 존재
- JSON blob inspect가 쉬움
- 비용/단순성 적절

## 단점
- 고급 query/search 기능 없음
- lease primitive를 그대로 쓰지 않으면 custom logic 필요
- 대규모 multi-poller에선 Table/Cosmos가 더 적합할 수 있음

## 후속
v0.4에 Table/Cosmos store 추가 검토.
