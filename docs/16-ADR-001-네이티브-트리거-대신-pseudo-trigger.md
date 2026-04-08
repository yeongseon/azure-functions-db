# ADR-001: 네이티브 트리거 대신 pseudo trigger 선택

## 상태
Accepted

## 문맥

Azure Functions에서 HTTP와 timer는 런타임 내장이고, 그 외 다수의 trigger/binding은
별도 extension 패키지/extension bundle을 통해 제공된다.
새 DB trigger를 범용적으로 native extension으로 만드는 것은 초기 비용과 유지보수 비용이 매우 크다.

## 결정

MVP는 Azure Functions native timer trigger 위에 구축되는 **pseudo trigger** 모델을 채택한다.

## 이유

- Python 중심으로 빠르게 시작 가능
- .NET custom extension 작성 불필요
- DB 범용성 확보 쉬움
- 로컬 재현성 높음
- semantics를 라이브러리에서 통제 가능

## 결과

장점:
- 빠른 구현
- 쉬운 디버깅
- 넓은 DB reach

단점:
- real-time push 아님
- duplicate 가능
- delete 감지 한계

## 후속
향후 특정 DB에 대해 native capability를 추가하더라도 public API는 유지한다.
