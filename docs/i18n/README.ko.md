# FlowMesh

<p align="center">
  <img src="https://img.shields.io/badge/상태-프로덕션%20준비%20완료-00C853?style=for-the-badge&logo=statuspage&logoColor=white" alt="Production Ready" />
  <img src="https://img.shields.io/badge/아키텍처-3티어%20하이브리드%20클라우드-007ACC?style=for-the-badge&logo=diagramsdotnet&logoColor=white" alt="3-Tier Architecture" />
  <img src="https://img.shields.io/badge/라이선스-Apache%202.0-blue?style=for-the-badge&logo=apache&logoColor=white" alt="Apache 2.0" />
</p>

<p align="center">
  <b> 언어 / Language / 语言 / 言語 / भाषा / Langue / Idioma:</b><br>
  <a href="../../README.md">English</a> •
  <a href="./README.ja.md">日本語</a> •
  <a href="./README.zh.md">简体中文</a> •
  <a href="./README.hi.md">हिन्दी</a> •
  <a href="./README.fr.md">Français</a> •
  <b>한국어</b> •
  <a href="./README.es.md">Español</a>
</p>

---

> **FlowMesh는 자체 호스팅이 가능하며 클라우드 종속성이 없는 오픈소스 엔터프라이즈 통합 및 분산 워크플로우 오케스트레이션 플랫폼입니다.**
> 사내 방화벽의 인바운드 포트를 열지 않고도 온프레미스 데이터베이스, 레거시 ERP 시스템(SAP, Oracle), 사내 마이크로서비스, SaaS API를 관측 가능하고 장애 복구 및 재실행이 가능한 DAG 워크플로우로 통합합니다.

---

## 목차

- [경영진 요약 (Executive Summary)](#-경영진-요약-executive-summary)
- [왜 FlowMesh인가?](#-왜-flowmesh인가)
- [핵심 역량 및 아키텍처 원칙](#-핵심-역량-및-아키텍처-원칙)
- [시스템 아키텍처](#-시스템-아키텍처)
- [모노레포 디렉터리 구조](#-모노레포-디렉터리-구조)
- [빠른 시작 가이드](#-빠른-시작-가이드)
  - [사전 요구사항](#사전-요구사항)
  - [옵션 A: 프로덕션 Docker Compose 스택 (권장)](#옵션-a-프로덕션-docker-compose-스택-권장)
  - [옵션 B: 로컬 베어메탈 개발 환경](#옵션-b-로컬-베어메탈-개발-환경)
  - [옵션 C: Kubernetes 및 Helm 배포](#옵션-c-kubernetes-및-helm-배포)
  - [옵션 D: 보안 엣지 에이전트 설치 (Linux systemd)](#옵션-d-보안-엣지-에이전트-설치-linux-systemd)
- [핵심 기능 모듈](#-핵심-기능-모듈)
- [분산 옵저버빌리티 및 텔레메트리](#-분산-옵저버빌리티-및-텔레메트리)
- [API 게이트웨이 레퍼런스](#-api-게이트웨이-레퍼런스)
- [아키텍처 결정 기록 (ADR)](#-아키텍처-결정-기록-adr)
- [테스트 및 자동 검증 스위트](#-테스트-및-자동-검증-스위트)
- [보안 및 규정 준수](#-보안-및-규정-준수)
- [기여 및 라이선스](#-기여-및-라이선스)

---

## 경영진 요약 (Executive Summary)

현대 기업의 IT 인프라는 레거시 ERP(SAP, Oracle), 최신 클라우드 데이터 웨어하우스, 관계형 데이터베이스(PostgreSQL, MySQL), 메시지 브로커, 수많은 SaaS 서비스로 파편화되어 있습니다. 기존 통합 솔루션은 명확한 한계를 지닙니다:
1. **퍼블릭 SaaS iPaaS**(Zapier, Workato, MuleSoft Cloud): 민감한 사내 데이터 및 데이터베이스 접속 자격 증명을 외부 클라우드로 전송해야 하므로 엄격한 데이터 주권 규정(GDPR, HIPAA, SOC 2)을 위반합니다.
2. **무거운 레거시 엔터프라이즈 미들웨어**: 수십만 달러에 달하는 고가의 라이선스 비용, 벤더 종속성 및 운영 복잡성.
3. **자체 개발한 임시 스크립트 및 Cron**: 분산 트레이싱, 스키마 변경 감지, 트랜잭션 복구, 멀티테넌트 격리 기능의 부재.

**FlowMesh는 이 딜레마를 해결합니다.** Python (FastAPI), Go, Next.js 15, NATS JetStream 및 PostgreSQL/Redis를 기반으로 구축되어 외부 클라우드 런타임 종속성 없이 엔터프라이즈급 고성능 통합 백본을 제공합니다.

---

## 왜 FlowMesh인가?

| 주요 기능 | FlowMesh | 클라우드 SaaS iPaaS | 레거시 엔터프라이즈 ESB | 자체 개발 스크립트 |
| :--- | :---: | :---: | :---: | :---: |
| **데이터 주권** | **100% 자체 호스팅** | 클라우드 멀티테넌트 | 사내 구축형 | 자체 호스팅 |
| **방화벽 인바운드 포트** | **0개 (아웃바운드 mTLS만 사용)**| 인바운드 포트 개방 필요 | 복잡한 전용선/VPN | 다양함 |
| **실행 보안** | **임의 RCE 배제 (암호화 서명)**| 원격 코드 실행 허용 | 무거운 JVM 플러그인 | 감사되지 않은 스크립트 |
| **상태 관리 엔진** | **Redis / RediForge / 메모리**| 독점 블랙박스 스토리지 | 관계형 DB 병목 | 상태 추적 불가 |
| **옵저버빌리티** | **W3C OpenTelemetry 기본 지원**| 벤더 제공 콘솔 한정 | 복잡한 JMX 도구 | 단순 파일 로그 |
| **라이선스 비용** | **무료 (Apache 2.0)** | 연간 5만~25만 달러 | 고액 다년 계약 필요 | 막대한 유지보수 공수 |

---

## 핵심 역량 및 아키텍처 원칙

- **인바운드 공격 표면 제로 ([ADR-0001](docs/adr/ADR-0001-agent-outbound-only.md))**: FlowMesh 엣지 에이전트는 아웃바운드 전용 mTLS/WebSocket 터널을 통해 제어 평면을 폴링합니다. 기업 방화벽에 수신 포트를 개방할 필요가 전혀 없습니다.
- **암호화 서명 기반의 구조화된 액션 ([ADR-0002](docs/adr/ADR-0002-no-remote-code-execution.md))**: 원격 코드 실행(RCE) 위험을 완전히 제거했습니다. 모든 작업은 Ed25519 서명 검증 및 로컬 화이트리스트 정책에 따라 검증된 선언적 커넥터 작업만 실행합니다.
- **플러그형 StateStore 추상화 ([ADR-0003](docs/adr/ADR-0003-statestore-abstraction.md))**: Redis, 고성능 RediForge 및 인메모리 스토리지를 일관된 인터페이스로 지원하며 원자적 분산 락 및 서킷 브레이커를 제공합니다.
- **불변 워크플로우 버전 관리 ([ADR-0004](docs/adr/ADR-0004-immutable-workflow-versions.md))**: 배포 시 불변의 $N+1$ 버전을 생성합니다. 실행 중인 인스턴스는 해당 고정 버전에서 안전하게 완료되며, 롤백 시 다운타임 없이 활성 포인터를 $N-1$로 즉시 전환합니다.
- **봉투 암호화(Envelope Encryption) 기반 자격 증명 보호**: 마스터 키(KEK)가 테넌트별 데이터 암호화 키(DEK)를 AES-256-GCM으로 동적 복호화합니다. 비밀번호가 평문으로 저장되거나 로그에 노출되지 않습니다.
- **멀티테넌트 행 수준 격리**: `TenantScopedRepository` 패턴을 통해 모든 데이터베이스 쿼리에서 테넌트 식별자 격리를 강제하여 데이터 유출을 방지합니다.

---

## 시스템 아키텍처

```text
                                  FLOWMESH ARCHITECTURE
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
             제어 평면 (포트 8000)                       데이터 평면 엔진
              FastAPI / Python 3.12+                   워크플로우 상태 머신
          ├── 17개 도메인 라우터                   ├── 위상 정렬 DAG 리졸버
          ├── RBAC & 인증 가드                    ├── 스텝 디스패처 & 재시도 관리
          └── TenantScopedRepository              └── 서킷 브레이커 & DLQ
                       │                                         │
                       ├────────────────────┬────────────────────┤
                       ▼                    ▼                    ▼
                NATS JetStream        PostgreSQL 16         Redis / RediForge
               (이벤트 버스 & DLQ)       (시스템 저장소)        (상태 저장소 & 락)
                       │                    │                    │
                       └────────────────────┼────────────────────┘
                                            │
                                   mTLS / 아웃바운드 풀
                                    (인바운드 포트 제로)
                                            │
                       ┌────────────────────▼────────────────────┐
                       │               고객사 내부망 / VPC        │
                       │                                         │
                       │           FLOWMESH 엣지 에이전트        │
                       │           (Go 1.23 정적 데몬)           │
                       │  ├── 로컬 정책 엔진 (기본 거부)         │
                       │  ├── 오프라인 SQLite 스풀 버퍼          │
                       │  ├── Ed25519 암호화 서명 검증기         │
                       │  └── 샌드박스 커넥터 런타임             │
                       │                                         │
                       │   ┌────────────┬───────────┬─────────┐  │
                       │   ▼            ▼           ▼         ▼  │
                       │ Postgres   REST APIs   Stripe/SAP  SFTP │
                       └─────────────────────────────────────────┘
```

상세 기술 사양은 [ARCHITECTURE.ko.md](./ARCHITECTURE.ko.md)를 참조하십시오.

---

## 빠른 시작 가이드

### 사전 요구사항
- **Python**: `3.12+` (`uv` 또는 `pip`)
- **Node.js**: `20 LTS+` (패키지 매니저: `pnpm 9+`)
- **Go**: `1.23+` (에이전트 데몬 빌드용)
- **Docker**: `24+` 및 Compose `v2+`

### 옵션 A: 프로덕션 Docker Compose 스택 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/your-org/flowmesh.git
cd flowmesh

# 2. 환경 변수 초기화
cp .env.example .env

# 3. Docker Compose로 모든 서비스 시작
docker compose up -d

# 4. 데모 데이터, 커넥터, 워크플로우 초기화
python seed_demo.py
```

#### 서비스 접근 URL 및 기본 계정

| 서비스 | URL | 기본 자격 증명 | 설명 |
| :--- | :--- | :--- | :--- |
| **웹 콘솔** | `http://localhost:3000` | 자동 로그인 | Next.js 15 엔터프라이즈 관리 UI |
| **워크플로우 스튜디오** | `http://localhost:3000/workflows` | — | 시각적 DAG 빌더 및 실행 |
| **실행 기록 & AI 진단** | `http://localhost:3000/runs` | — | 트레이스 및 장애 원인 분석 |
| **커넥션 & 드리프트** | `http://localhost:3000/connections` | — | 스키마 검색 및 변경점 비교 |
| **옵저버빌리티** | `http://localhost:3000/observability` | — | 통합 모니터링 및 텔레메트리 |
| **Swagger API 문서** | `http://localhost:8000/docs` | `bearer demo-token` | 대화형 OpenAPI 문서 |
| **헬스체크** | `http://localhost:8000/health` | 공개 | 인스턴스 활성 상태 프로브 |
| **Prometheus 메트릭** | `http://localhost:8000/metrics` | 공개 | OpenMetrics 수집 엔드포인트 |
| **Grafana 대시보드** | `http://localhost:3001` | `admin` / `admin` | 모니터링 대시보드 |

---

## 아키텍처 결정 기록 (ADR)

- **[ADR-0001: 엣지 에이전트 아웃바운드 전용 아키텍처](docs/adr/ADR-0001-agent-outbound-only.md)** — 고객사 방화벽 인바운드 포트 0개 유지.
- **[ADR-0002: 임의 원격 코드 실행(RCE) 배제](docs/adr/ADR-0002-no-remote-code-execution.md)** — 암호화 서명 및 선언적 커넥터 작업 모델.
- **[ADR-0003: Redis 및 RediForge용 범용 StateStore 추상화](docs/adr/ADR-0003-statestore-abstraction.md)** — 분산 락 및 서킷 브레이커 통합.
- **[ADR-0004: 불변 워크플로우 버전 관리 및 핀 고정](docs/adr/ADR-0004-immutable-workflow-versions.md)** — 안전한 무중단 롤백 보장.

---

## 라이선스

FlowMesh는 **Apache License, Version 2.0** 라이선스 하에 배포되는 오픈소스 소프트웨어입니다.
자세한 내용은 [LICENSE](LICENSE) 파일을 참조하십시오.
