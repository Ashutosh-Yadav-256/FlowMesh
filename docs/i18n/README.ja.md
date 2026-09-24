# FlowMesh

<p align="center">
  <img src="https://img.shields.io/badge/ステータス-本番運用可能-00C853?style=for-the-badge&logo=statuspage&logoColor=white" alt="Production Ready" />
  <img src="https://img.shields.io/badge/アーキテクチャ-3層ハイブリッドクラウド-007ACC?style=for-the-badge&logo=diagramsdotnet&logoColor=white" alt="3-Tier Architecture" />
  <img src="https://img.shields.io/badge/ライセンス-Apache%202.0-blue?style=for-the-badge&logo=apache&logoColor=white" alt="Apache 2.0" />
</p>

<p align="center">
  <b> 言語 / Language / 语言 / भाषा / Langue / 언어 / Idioma:</b><br>
  <a href="../../README.md">English</a> •
  <b>日本語</b> •
  <a href="./README.zh.md">简体中文</a> •
  <a href="./README.hi.md">हिन्दी</a> •
  <a href="./README.fr.md">Français</a> •
  <a href="./README.ko.md">한국어</a> •
  <a href="./README.es.md">Español</a>
</p>

---

> **FlowMeshは、セルフホスト可能でクラウドに依存せず、ベンダーロックインのないエンタープライズ向けインテグレーションおよび分散ワークフローオーケストレーション基盤です。**
> 企業内ファイアウォールに穴を開けることなく、オンプレミスデータベース、レガシーERP、内部マイクロサービス、SaaS APIを、観測可能・耐障害性・再生可能なDAGワークフローへと統合します。

---

## 目次

- [エグゼクティブサマリー](#-エグゼクティブサマリー)
- [なぜFlowMeshなのか？](#-なぜflowmeshなのか)
- [主要機能とアーキテクチャ原則](#-主要機能とアーキテクチャ原則)
- [システムアーキテクチャ](#-システムアーキテクチャ)
- [リポジトリ構成](#-リポジトリ構成)
- [クイックスタートガイド](#-クイックスタートガイド)
  - [前提条件](#前提条件)
  - [方法A: 本番用Docker Compose環境（推奨）](#方法a-本番用docker-compose環境推奨)
  - [方法B: ローカルベアメタル開発環境](#方法b-ローカルベアメタル開発環境)
  - [方法C: Kubernetes & Helm デプロイ](#方法c-kubernetes--helm-デプロイ)
  - [方法D: エッジエージェント導入（Linux systemd）](#方法d-エッジエージェント導入linux-systemd)
- [主要コアモジュール](#-主要コアモジュール)
- [分散オブザーバビリティとテレメトリ](#-分散オブザーバビリティとテレメトリ)
- [APIゲートウェイリファレンス](#-apiゲートウェイリファレンス)
- [アーキテクチャ決定記録 (ADR)](#-アーキテクチャ決定記録-adr)
- [テストと自動検証スイート](#-テストと自動検証スイート)
- [セキュリティとコンプライアンス](#-セキュリティとコンプライアンス)
- [コントリビューションとライセンス](#-コントリビューションとライセンス)

---

## エグゼクティブサマリー

現代の企業インフラは、レガシーERP（SAP、Oracle）、最新のクラウドデータウェアハウス、リレーショナルDB（PostgreSQL、MySQL）、メッセージブローカー、サードパーティSaaSの間で深刻な分断を抱えています。従来のインテグレーション手段には重大な課題が存在します：
1. **パブリックSaaS iPaaS**（Zapier、Workato、MuleSoft Cloudなど）：機密データや認証情報を社外に送信する必要があり、厳格なデータ主権（GDPR、HIPAA、SOC 2）に抵触します。
2. **重厚なレガシーミドルウェア**：莫大なライセンス費用、ベンダーロックイン、運用の複雑さ。
3. **内製のCron/独自スクリプト**：分散トレーシング、スキーマドリフト検知、トランザクション回復、マルチテナント分離の欠如。

**FlowMeshはこのジレンマを解消します。** Python (FastAPI)、Go、Next.js 15、NATS JetStream、PostgreSQL/Redisを基盤とした、高スループットかつクラウドアグノスティックな統合バックボーンを提供します。

---

## なぜFlowMeshなのか？

| 機能・要件 | FlowMesh | クラウドSaaS iPaaS | レガシーエンタープライズESB | 自社製スクリプト |
| :--- | :---: | :---: | :---: | :---: |
| **データ主権** | **100% 自社ホスト** | クラウドマルチテナント | オンプレミス | 自社ホスト |
| **ファイアウォール受信ポート** | **ゼロ（送信mTLSのみ）** | 受信ポート・Bastion必須 | 複雑な専用線/VPN | 個別対応 |
| **実行セキュリティ** | **任意RCEの排除（署名必須）** | リモートコード実行可能 | 重厚なJVMプラグイン | 監査なしスクリプト |
| **ステート管理** | **Redis / RediForge / メモリ** | 独自ブラックボックス | RDBのボトルネック | 状態管理なし |
| **オブザーバビリティ** | **W3C OpenTelemetry標準** | ベンダー専用画面のみ | 複雑なJMXツール | 標準ログのみ |
| **ライセンスコスト** | **無償（Apache 2.0）** | 年間数百万〜数千万円 | 高額な複数年契約 | 膨大な保守開発コスト |

---

## 主要機能とアーキテクチャ原則

- **受信ゼロのアタックサーフェス ([ADR-0001](docs/adr/ADR-0001-agent-outbound-only.md))**: FlowMeshエッジエージェントは、送信専用のmTLS/WebSocketトンネル経由でコントロールプレーンをポーリングします。ファイアウォールの受信ポートは一切開放不要です。
- **暗号署名付き構造化アクション ([ADR-0002](docs/adr/ADR-0002-no-remote-code-execution.md))**: 任意コード実行（RCE）を根絶。すべてのタスクはローカルEd25519署名とホワイトリストで検証された宣言的コネクタアクションのみを実行します。
- **プラグ可能ステートストア抽象化 ([ADR-0003](docs/adr/ADR-0003-statestore-abstraction.md))**: Redis、超高速RediForge、およびインメモリキャッシュを共通インターフェースでサポート。アトミックな分散ロックとサーキットブレーカーを内蔵。
- **不変ワークフローバージョニング ([ADR-0004](docs/adr/ADR-0004-immutable-workflow-versions.md))**: デプロイ時に不変の$N+1$バージョンを生成。実行中インスタンスは固定バージョンで完了し、ロールバック時はダウンタイムなしでアクティブポインタを$N-1$に戻します。
- **エンベロープ暗号化による認証情報保護**: マスター暗号鍵（KEK）がテナントデータ暗号鍵（DEK）をAES-256-GCMで動的に復号。機密値が平文で保存されたりログに出力されることはありません。
- **マルチテナント行レベル分離**: `TenantScopedRepository`パターンにより、全DB操作でテナント境界を強制し、テナント間のデータ漏洩を防止します。
- **高信頼性メッセージパイプライン**: NATS JetStreamによる確実なアットリーストワンス配信、重複排除、ジッター付き指数バックオフ再試行、およびデッドレターキュー（DLQ）。
- **自動スキーマドリフト検知**: 企業内データベースのスキーマ変化を検知し、安全な追加（`WARNING`）と破壊的変更（`CRITICAL`）に自動分類します。

---

## システムアーキテクチャ

```text
                                  FLOWMESH ARCHITECTURE
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
           コントロールプレーン (ポート 8000)               データプレーンエンジン
              FastAPI / Python 3.12+                  ワークフローステートマシン
          ├── 17のドメインルーター                 ├── トポロジカルDAGリゾルバ
          ├── RBAC & 認証ガード                   ├── ステップディスパッチャ & 再試行
          └── TenantScopedRepository              └── サーキットブレーカー & DLQ
                       │                                         │
                       ├────────────────────┬────────────────────┤
                       ▼                    ▼                    ▼
                NATS JetStream        PostgreSQL 16         Redis / RediForge
             (イベントバス & DLQ)       (正規データストア)       (状態管理 & ロック)
                       │                    │                    │
                       └────────────────────┼────────────────────┘
                                            │
                                   mTLS / 送信プル通信
                                    (受信ポート ゼロ)
                                            │
                       ┌────────────────────▼────────────────────┐
                       │             顧客プライベートNW          │
                       │                                         │
                       │          FLOWMESH エッジエージェント    │
                       │           (Go 1.23 スタティックバイナリ) │
                       │  ├── ローカルポリシーエンジン (拒否優先)│
                       │  ├── ローカルSQLiteスプールバッファ     │
                       │  ├── 暗号署名検証 (Ed25519)             │
                       │  └── サンドボックスコネクタランタイム   │
                       │                                         │
                       │   ┌────────────┬───────────┬─────────┐  │
                       │   ▼            ▼           ▼         ▼  │
                       │ Postgres   REST APIs   Stripe/SAP  SFTP │
                       └─────────────────────────────────────────┘
```

詳細な技術仕様については [ARCHITECTURE.ja.md](./ARCHITECTURE.ja.md) をご覧ください。

---

## クイックスタートガイド

### 前提条件
- **Python**: `3.12+` (`uv` または `pip`)
- **Node.js**: `20 LTS+` (`pnpm 9+`)
- **Go**: `1.23+` (エッジエージェントビルド用)
- **Docker**: `24+` & Compose `v2+`

### 方法A: 本番用Docker Compose環境（推奨）

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/flowmesh.git
cd flowmesh

# 2. 環境変数の初期化
cp .env.example .env

# 3. Docker Composeで全コンポーネントを起動
# (PostgreSQL 16, NATS JetStream, Redis 7, API Gateway, Web Console, Prometheus, Grafana)
docker compose up -d

# 4. デモテナント、認証情報、コネクタ、ワークフローの初期投入
python seed_demo.py
```

#### サービス接続情報

| サービス | URL | 認証情報 | 説明 |
| :--- | :--- | :--- | :--- |
| **Webコンソール** | `http://localhost:3000` | 認証済み | Next.js 15 エンタープライズ管理画面 |
| **ワークフロースタジオ** | `http://localhost:3000/workflows` | — | ビジュアルDAGビルダー & 実行 |
| **実行履歴とAI診断** | `http://localhost:3000/runs` | — | トレース閲覧 & AIインシデント解析 |
| **接続とドリフト検知** | `http://localhost:3000/connections` | — | スキーマディスカバリと差分比較 |
| **オブザーバビリティ** | `http://localhost:3000/observability` | — | メトリクス・ログ・テレメトリ画面 |
| **Swagger API文書** | `http://localhost:8000/docs` | `bearer demo-token` | 対話型OpenAPIエクスプローラー |
| **ヘルスチェック** | `http://localhost:8000/health` | 認証不要 | 生存確認プローブ |
| **Prometheusメトリクス**| `http://localhost:8000/metrics` | 認証不要 | OpenMetricsスクレイピングエンドポイント |
| **Grafanaダッシュボード**| `http://localhost:3001` | `admin` / `admin` | 本番監視ダッシュボード |

---

## アーキテクチャ決定記録 (ADR)

- **[ADR-0001: エージェントの送信専用アーキテクチャ](docs/adr/ADR-0001-agent-outbound-only.md)** — ファイアウォール受信ポートゼロの実現。
- **[ADR-0002: 任意のリモートコード実行の排除](docs/adr/ADR-0002-no-remote-code-execution.md)** — 暗号署名付き構造化コネクタ呼び出しの強制。
- **[ADR-0003: RedisおよびRediForge用ステートストア抽象化](docs/adr/ADR-0003-statestore-abstraction.md)** — 分散ロックとサーキットブレーカーを統合した状態管理。
- **[ADR-0004: 不変ワークフローバージョニングとピン留め](docs/adr/ADR-0004-immutable-workflow-versions.md)** — 実行中インスタンスの安定完了と即時ロールバック保証。

---

## ライセンス

FlowMeshは **Apache License, Version 2.0** の下で公開されているオープンソースソフトウェアです。
詳細は [LICENSE](LICENSE) をご参照ください。
