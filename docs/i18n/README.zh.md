# FlowMesh

<p align="center">
  <img src="https://img.shields.io/badge/状态-生产就绪-00C853?style=for-the-badge&logo=statuspage&logoColor=white" alt="Production Ready" />
  <img src="https://img.shields.io/badge/架构-三层混合云-007ACC?style=for-the-badge&logo=diagramsdotnet&logoColor=white" alt="3-Tier Architecture" />
  <img src="https://img.shields.io/badge/开源协议-Apache%202.0-blue?style=for-the-badge&logo=apache&logoColor=white" alt="Apache 2.0" />
</p>

<p align="center">
  <b> 语言 / Language / 言語 / भाषा / Langue / 언어 / Idioma:</b><br>
  <a href="../../README.md">English</a> •
  <a href="./README.ja.md">日本語</a> •
  <b>简体中文</b> •
  <a href="./README.hi.md">हिन्दी</a> •
  <a href="./README.fr.md">Français</a> •
  <a href="./README.ko.md">한국어</a> •
  <a href="./README.es.md">Español</a>
</p>

---

> **FlowMesh 是一个开源、私有化部署、无厂商锁定的企业级集成与分布式工作流编排平台。**
> 它能够在无需穿透企业内网防火墙的前提下，将本地数据库、传统ERP系统、内部微服务以及各类 SaaS API 统一为具备完全可观测性、故障容错与重放能力的 DAG 工作流。

---

## 目录

- [执行摘要](#-执行摘要)
- [为什么选择 FlowMesh？](#-为什么选择-flowmesh)
- [核心能力与架构原则](#-核心能力与架构原则)
- [系统架构图](#-系统架构图)
- [Monorepo 目录结构](#-monorepo-目录结构)
- [快速入门指南](#-快速入门指南)
  - [环境准备](#环境准备)
  - [方案 A: 生产级 Docker Compose 全栈（推荐）](#方案-a-生产级-docker-compose-全栈推荐)
  - [方案 B: 本地裸机开发模式](#方案-b-本地裸机开发模式)
  - [方案 C: Kubernetes 与 Helm 部署](#方案-c-kubernetes-与-helm-部署)
  - [方案 D: 边缘 Agent 守护进程部署（Linux systemd）](#方案-d-边缘-agent-守护进程部署linux-systemd)
- [核心功能模块](#-核心功能模块)
- [分布式可观测性与遥测](#-分布式可观测性与遥测)
- [API 网关路由参考](#-api-网关路由参考)
- [架构决策记录 (ADR)](#-架构决策记录-adr)
- [测试与自动化验证套件](#-测试与自动化验证套件)
- [安全性与合规性](#-安全性与合规性)
- [开源协议与参与贡献](#-开源协议与参与贡献)

---

## 执行摘要

现代企业的基础设施分布极为零散：传统核心 ERP（SAP、Oracle）、云数据仓库、关系型数据库（PostgreSQL、MySQL）、消息总线及海量第三方 SaaS。现有的集成方案存在不可忽视的妥协：
1. **公有云 SaaS iPaaS**（如 Zapier、Workato、MuleSoft Cloud）：要求将高度敏感的企业数据和凭证传输到外部云端，直接违反严苛的数据主权法规（如 GDPR、HIPAA、等保）。
2. **重型传统 ESB 中间件**：动辄数十万甚至数百万美元授权费用，高昂的维护成本以及深度的厂商绑定。
3. **自研脚本与定时任务**：缺乏分布式链路追踪、模式演进（Schema Drift）治理、事务级状态恢复以及细粒度多租户隔离。

**FlowMesh 彻底解决了这一核心难题。** 平台采用 Python (FastAPI)、Go、Next.js 15、NATS JetStream 和 PostgreSQL/Redis 构建，完全开源自托管，零外部云运行时依赖。

---

## 为什么选择 FlowMesh？

| 特性 / 考量点 | FlowMesh | 公有云 SaaS iPaaS | 传统企业级 ESB | 自研胶水代码 / 脚本 |
| :--- | :---: | :---: | :---: | :---: |
| **数据主权** | **100% 本地自托管** | 云端多租户托管 | 本地部署 | 本地部署 |
| **防火墙入站端口** | **零端口（仅出站 mTLS）**| 需开放端口 / 堡垒机 | 复杂专线或 VPN | 难以统一管控 |
| **执行安全** | **杜绝任意 RCE（加密签名）**| 允许远程执行代码 | 笨重的 JVM 插件 | 未经审计的自由脚本 |
| **状态引擎** | **Redis / RediForge / 内存**| 黑盒专有状态存储 | 数据库瓶颈明显 | 缺少状态追踪机制 |
| **可观测性** | **W3C OpenTelemetry 原生**| 仅限厂商控制台 | 复杂的 JMX 监控 | 散落的文本日志 |
| **授权成本** | **完全免费 (Apache 2.0)** | 每年数万至数十万美元 | 高昂的多年合同绑定 | 沉重的长期维护人力 |

---

## 核心能力与架构原则

- **零入站攻击面 ([ADR-0001](docs/adr/ADR-0001-agent-outbound-only.md))**: FlowMesh 边缘 Agent 仅通过纯出站长连接（mTLS/WebSocket）向控制平面轮询任务，企业内网无需开放任何入站监听端口。
- **杜绝任意远程代码执行 ([ADR-0002](docs/adr/ADR-0002-no-remote-code-execution.md))**: 彻底消除 RCE 隐患。所有步骤均为强类型结构化 Connector 调用，必须通过 Ed25519 签名与本地白名单策略校验。
- **可插拔 StateStore 状态抽象 ([ADR-0003](docs/adr/ADR-0003-statestore-abstraction.md))**: 统一定义分布式租约、分布式锁和熔断器状态，无缝支持 Redis、超低延迟 RediForge 和内存存储。
- **不可变工作流版本控制 ([ADR-0004](docs/adr/ADR-0004-immutable-workflow-versions.md))**: 每次发布均生成固化 $N+1$ 版本；运行中实例严格执行于原版本，回滚时仅需瞬时切换活动指针至 $N-1$。
- **信封加密敏感凭据**: 主密钥（KEK）动态解密租户数据密钥（DEK），所有数据库密码与 API Key 均以 AES-256-GCM 密文存储，日志彻底脱敏。
- **多租户行级强制隔离**: 采用 `TenantScopedRepository` 架构设计，在数据持久层强制绑定租户标识，从根源杜绝越权访问。
- **高韧性消息底座**: 借助 NATS JetStream 实现持久化至少一次递送、确定性防重去重、带抖动的指数退避重试与死信队列（DLQ）。
- **自动化 Schema 漂移检测**: 持续探查外部系统数据模式变化，智能判定非破坏性变更（`WARNING`）与破坏性变更（`CRITICAL`）。

---

## 系统架构图

```text
                                  FLOWMESH ARCHITECTURE
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
              控制平面 (端口 8000)                       数据平面引擎
              FastAPI / Python 3.12+                  工作流状态机运行时
          ├── 17 个专业领域路由                   ├── 拓扑排序 DAG 解析器
          ├── RBAC 与鉴权中间件                   ├── 步骤分发与退避重试
          └── TenantScopedRepository              └── 分布式熔断器与死信队列
                       │                                         │
                       ├────────────────────┬────────────────────┤
                       ▼                    ▼                    ▼
                NATS JetStream        PostgreSQL 16         Redis / RediForge
               (事件总线与 DLQ)          (系统真实数据源)        (状态存储与分布式锁)
                       │                    │                    │
                       └────────────────────┼────────────────────┘
                                            │
                                   mTLS / 纯出站拉取
                                     (零入站端口)
                                            │
                       ┌────────────────────▼────────────────────┐
                       │               客户企业内网 / VPC        │
                       │                                         │
                       │          FLOWMESH 边缘 AGENT            │
                       │         (Go 1.23 静态编译守护进程)      │
                       │  ├── 本地策略引擎 (默认全阻断)          │
                       │  ├── 本地 SQLite 断网持久化缓冲         │
                       │  ├── 密码学 Ed25519 签名校验器          │
                       │  └── 沙箱化 Connector 连接器执行环境    │
                       │                                         │
                       │   ┌────────────┬───────────┬─────────┐  │
                       │   ▼            ▼           ▼         ▼  │
                       │ Postgres   REST APIs   Stripe/SAP  SFTP │
                       └─────────────────────────────────────────┘
```

详细技术规格请参阅 [ARCHITECTURE.zh.md](./ARCHITECTURE.zh.md)。

---

## 快速入门指南

### 环境准备
- **Python**: `3.12+` (支持 `uv` 或 `pip`)
- **Node.js**: `20 LTS+` (包管理器: `pnpm 9+`)
- **Go**: `1.23+` (用于编译 Edge Agent)
- **Docker**: `24+` 与 Compose `v2+`

### 方案 A: 生产级 Docker Compose 全栈（推荐）

```bash
# 1. 克隆代码仓库
git clone https://github.com/your-org/flowmesh.git
cd flowmesh

# 2. 初始化环境变量
cp .env.example .env

# 3. 启动所有容器服务 (Postgres 16, NATS JetStream, Redis 7, API, Web, Prometheus, Grafana)
docker compose up -d

# 4. 导入演示租户、凭证、连接器与示例工作流
python seed_demo.py
```

#### 服务访问信息

| 服务名称 | 访问地址 | 默认认证 | 功能说明 |
| :--- | :--- | :--- | :--- |
| **Web 控制台** | `http://localhost:3000` | 免密登录 | Next.js 15 企业级管理前台 |
| **工作流编排器** | `http://localhost:3000/workflows` | — | 可视化 DAG 设计与触发 |
| **执行记录与 AI 诊断** | `http://localhost:3000/runs` | — | 追踪详情与 AI 故障分析 |
| **连接与漂移监控** | `http://localhost:3000/connections` | — | 模式发现与差异对比 |
| **可观测性大屏** | `http://localhost:3000/observability` | — | 监控指标与全链路追踪 |
| **Swagger API 文档** | `http://localhost:8000/docs` | `bearer demo-token` | 交互式 OpenAPI 接口测试 |
| **健康探针** | `http://localhost:8000/health` | 公开 | 存活探针状态检测 |
| **Prometheus 指标** | `http://localhost:8000/metrics` | 公开 | 标准 OpenMetrics 采集接口 |
| **Grafana 监控面板** | `http://localhost:3001` | `admin` / `admin` | 生产级综合监控大盘 |

---

## 架构决策记录 (ADR)

- **[ADR-0001: 边缘 Agent 纯出站通信架构](docs/adr/ADR-0001-agent-outbound-only.md)** — 内网零入站端口开放。
- **[ADR-0002: 全面拒绝任意远程代码执行](docs/adr/ADR-0002-no-remote-code-execution.md)** — 采用加密签名与强类型连接器模型。
- **[ADR-0003: Redis 与 RediForge 统一状态存储抽象](docs/adr/ADR-0003-statestore-abstraction.md)** — 分布式锁与熔断器机制。
- **[ADR-0004: 不可变工作流版本控制与固定执行](docs/adr/ADR-0004-immutable-workflow-versions.md)** — 平滑灰度与零停机回滚。

---

## 开源协议

FlowMesh 遵循 **Apache License 2.0** 开源许可协议。
详情请参阅 [LICENSE](LICENSE) 文件。
