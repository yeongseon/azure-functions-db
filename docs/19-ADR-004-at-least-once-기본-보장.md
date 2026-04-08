# ADR-004: 기본 보장을 at-least-once로 정의

## 상태
Accepted

## 문맥

pseudo trigger 환경에서 exactly-once는 과도한 복잡성을 유발한다.
반면 누락 없는 처리가 더 중요하다.

## 결정

기본 contract를 **at-least-once에 가까운 delivery**로 정의한다.

## 이유

- batch success 후 commit 모델과 잘 맞음
- crash/commit failure 시 loss보다 duplicate를 허용하는 편이 안전
- 사용자에게 idempotent handler 요구를 명확히 전달 가능

## 결과
- handler 및 downstream은 중복 허용 설계 필요
- docs에서 exactly-once 오해를 방지해야 함
- dedup helper는 옵션으로 제공
