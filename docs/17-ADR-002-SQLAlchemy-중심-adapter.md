# ADR-002: SQLAlchemy 중심 adapter 채택

## 상태
Accepted

## 문맥

여러 RDBMS를 공통 API로 다루려면 dialect/driver 추상화가 필요하다.
이를 처음부터 직접 만들면 비용이 과하다.

## 결정

RDBMS 계열 MVP는 SQLAlchemy Core 기반 adapter를 채택한다.

## 이유

- PostgreSQL / MySQL / SQLite / Oracle / SQL Server 등 넓은 dialect 지원
- DBAPI/driver 차이를 숨기기 좋음
- reflection/query builder/parameter binding 재사용 가능
- ORM 없이 Core만 사용 가능

## 대안
1. DB별 raw driver 직접 지원
2. ORM 중심 설계
3. 완전 독자 query layer

## 선택 이유
SQLAlchemy Core가 가장 균형적이다.

## 결과
- RDBMS reach 빠르게 확보
- package extras로 driver 선택 가능
- Mongo 등 비SQL은 별도 adapter 유지
