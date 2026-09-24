# FlowMesh

<p align="center">
  <img src="https://img.shields.io/badge/Statut-Prêt%20pour%20la%20Production-00C853?style=for-the-badge&logo=statuspage&logoColor=white" alt="Production Ready" />
  <img src="https://img.shields.io/badge/Architecture-Cloud%20Hybride%203%20Tiers-007ACC?style=for-the-badge&logo=diagramsdotnet&logoColor=white" alt="3-Tier Architecture" />
  <img src="https://img.shields.io/badge/Licence-Apache%202.0-blue?style=for-the-badge&logo=apache&logoColor=white" alt="Apache 2.0" />
</p>

<p align="center">
  <b> Langue / Language / 语言 / 言語 / भाषा / 언어 / Idioma:</b><br>
  <a href="../../README.md">English</a> •
  <a href="./README.ja.md">日本語</a> •
  <a href="./README.zh.md">简体中文</a> •
  <a href="./README.hi.md">हिन्दी</a> •
  <b>Français</b> •
  <a href="./README.ko.md">한국어</a> •
  <a href="./README.es.md">Español</a>
</p>

---

> **FlowMesh est une plateforme open-source, auto-hébergée et agnostique au cloud pour l'intégration d'entreprise et l'orchestration de workflows distribués.**
> Elle unifie les bases de données sur site, les ERP historiques (SAP, Oracle), les microservices internes et les API SaaS dans des workflows DAG observables, tolérants aux pannes et rejouables, sans jamais ouvrir de port sur les pare-feu d'entreprise.

---

## Table des Matières

- [Synthèse Opérationnelle](#-synthèse-opérationnelle)
- [Pourquoi Choisir FlowMesh ?](#-pourquoi-choisir-flowmesh-)
- [Capacités Clés & Principes d'Architecture](#-capacités-clés--principes-darchitecture)
- [Architecture du Système](#-architecture-du-système)
- [Organisation du Monorepo](#-organisation-du-monorepo)
- [Guide de Démarrage Rapide](#-guide-de-démarrage-rapide)
  - [Prérequis](#prérequis)
  - [Option A : Pile Docker Compose de Production (Recommandée)](#option-a--pile-docker-compose-de-production-recommandée)
  - [Option B : Développement Local Bare-Metal](#option-b--développement-local-bare-metal)
  - [Option C : Déploiement Kubernetes & Helm](#option-c--déploiement-kubernetes--helm)
  - [Option D : Déploiement de l'Agent Edge Sécurisé (Linux systemd)](#option-d--déploiement-de-lagent-edge-sécurisé-linux-systemd)
- [Modules Fonctionnels Principaux](#-modules-fonctionnels-principaux)
- [Observabilité Distribuée & Télémétrie](#-observabilité-distribuée--télémétrie)
- [Référentiel des API Gateway](#-référentiel-des-api-gateway)
- [Registres de Décision d'Architecture (ADRs)](#-registres-de-décision-darchitecture-adrs)
- [Suite de Tests et Validation Automatisée](#-suite-de-tests-et-validation-automatisée)
- [Sécurité & Conformité](#-sécurité--conformité)
- [Contribution & Licence](#-contribution--licence)

---

## Synthèse Opérationnelle

Les infrastructures informatiques d'entreprise modernes sont profondément fragmentées : ERP historiques (SAP, Oracle), entrepôts de données cloud, bases relationnelles (PostgreSQL, MySQL), courtiers de messages et services SaaS tiers. Les solutions d'intégration actuelles imposent des compromis inacceptables :
1. **iPaaS SaaS Publics** (Zapier, Workato, MuleSoft Cloud) : imposent l'exportation de données d'entreprise hautement confidentielles et d'identifiants de bases de données, violant les réglementations strictes sur la souveraineté des données (RGPD, HIPAA, SOC 2).
2. **Middleware Propriétaire Lourd** : licences annuelles exorbitantes, enfermement propriétaire et complexité opérationnelle.
3. **Scripts et Tâches Cron Internes** : absence de traçage distribué, incapacité à gérer les dérives de schéma, pas de reprise après incident et isolation multi-tenant inexistante.

**FlowMesh élimine ces compromis.** Conçue sur Python (FastAPI), Go, Next.js 15, NATS JetStream et PostgreSQL/Redis, la plateforme fournit une dorsale d'intégration haute performance, sans coût de licence logiciel et sans dépendance à un cloud propriétaire.

---

## Pourquoi Choisir FlowMesh ?

| Capacité | FlowMesh | iPaaS Cloud SaaS | ESB d'Entreprise Hérité | Scripts Maison Ad-Hoc |
| :--- | :---: | :---: | :---: | :---: |
| **Souveraineté des Données** | **100% Auto-Hébergé** | Cloud Multi-Tenant | Sur Site | Auto-Hébergé |
| **Ports Inbound du Pare-Feu** | **Zéro (mTLS Sortant Uniquement)**| Ports Ouverts / Bastions requis | VPNs Dédiés Complexes | Variable |
| **Sécurité d'Exécution** | **Aucun RCE Arbitraire (Signé)** | Exécution de Code Distant | Plugins JVM Lourds | Scripts non audités |
| **Moteur d'État** | **Redis / RediForge / Mémoire** | Boîte Noire Propriétaire | Goulot d'étranglement RDB | Aucun état transactionnel |
| **Observabilité** | **W3C OpenTelemetry Natif** | Portail Fournisseur Uniquement | Outils JMX Obsolètes | Fichiers logs simples |
| **Coût de Licence** | **Gratuit (Apache 2.0)** | 50 k$ à 250 k$ / an | Contrats pluriannuels élevés | Coût de maintenance démesuré |

---

## Capacités Clés & Principes d'Architecture

- **Surface d'Attaque Inbound Nulle ([ADR-0001](docs/adr/ADR-0001-agent-outbound-only.md))** : Les agents Edge FlowMesh interrogent le plan de contrôle via des tunnels mTLS sortants exclusifs. Les pare-feu d'entreprise restent 100 % hermétiques.
- **Actions Déclaratives Cryptographiquement Signées ([ADR-0002](docs/adr/ADR-0002-no-remote-code-execution.md))** : Élimination absolue de toute Exécution Arbitraire de Code Distant (RCE). Chaque tâche exécute un connecteur validé par signature Ed25519 et filtré par liste blanche locale.
- **Abstraction StateStore Modulaire ([ADR-0003](docs/adr/ADR-0003-statestore-abstraction.md))** : Prise en charge transparente de Redis, RediForge et du stockage en mémoire avec verrous distribués atomiques et disjoncteurs (circuit breakers).
- **Gestion de Version Immuable des Workflows ([ADR-0004](docs/adr/ADR-0004-immutable-workflow-versions.md))** : Tout déploiement crée une version figée $N+1$. Les exécutions en cours terminent sur leur version dédiée ; les retours arrière (rollbacks) réalignent le pointeur actif sur $N-1$ sans arrêt de service.
- **Chiffrement Enveloppe des Secrets** : Une clé maîtresse (KEK) chiffre dynamiquement les clés de données spécifiques aux tenants (DEK) en AES-256-GCM. Aucun secret n'est jamais stocké en clair ou tracé dans les journaux.
- **Cloisonnement Multi-Tenant au Niveau des Lignes** : Le modèle `TenantScopedRepository` impose l'isolation obligatoire du `tenant_id` sur chaque transaction de base de données.
- **Pipeline de Messages Ultra-Résilient** : NATS JetStream assure la diffusion persistante avec garantie de livraison au moins une fois, déduplication stricte des messages et files de rebut (Dead Letter Queues - DLQ).
- **Détection Automatisée de Dérive de Schéma (Drift)** : Découverte continue des évolutions de modèles de données et classification intelligente en alertes mineures (`WARNING`) ou ruptures majeures (`CRITICAL`).

---

## Architecture du Système

```text
                                  FLOWMESH ARCHITECTURE
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
             PLAN DE CONTRÔLE (PORT 8000)               MOTEUR DU PLAN DE DONNÉES
               FastAPI / Python 3.12+                    Machine à États Distribuable
          ├── 17 Routeurs de Domaine                 ├── Résolveur Topologique DAG
          ├── RBAC & Garde d'Authentification        ├── Distributeur d'Étapes & Retries
          └── TenantScopedRepository                 └── Disjoncteur & Files DLQ
                       │                                         │
                       ├────────────────────┬────────────────────┤
                       ▼                    ▼                    ▼
                NATS JetStream        PostgreSQL 16         Redis / RediForge
              (Bus d'Événements)   (Système de Référence)   (StateStore & Verrous)
                       │                    │                    │
                       └────────────────────┼────────────────────┘
                                            │
                                   mTLS / Extraction Sortante
                                      (Zéro Port Entrant)
                                            │
                       ┌────────────────────▼────────────────────┐
                       │          RÉSEAU PRIVÉ CLIENT / VPC      │
                       │                                         │
                       │            FLOWMESH AGENT EDGE          │
                       │           (Démon Statique en Go)        │
                       │  ├── Moteur de Politiques Locales       │
                       │  ├── Tampon Déconnecté SQLite Local     │
                       │  ├── Vérificateur de Signature Ed25519  │
                       │  └── Exécution Sécurisée de Connecteurs │
                       │                                         │
                       │   ┌────────────┬───────────┬─────────┐  │
                       │   ▼            ▼           ▼         ▼  │
                       │ Postgres   APIs REST   Stripe/SAP  SFTP │
                       └─────────────────────────────────────────┘
```

Pour les spécifications techniques complètes, veuillez consulter [ARCHITECTURE.fr.md](./ARCHITECTURE.fr.md).

---

## Guide de Démarrage Rapide

### Prérequis
- **Python** : `3.12+` (avec `uv` ou `pip`)
- **Node.js** : `20 LTS+` (gestionnaire : `pnpm 9+`)
- **Go** : `1.23+` (requis pour compiler l'agent Edge)
- **Docker** : `24+` et Compose `v2+`

### Option A : Pile Docker Compose de Production (Recommandée)

```bash
# 1. Cloner le dépôt
git clone https://github.com/your-org/flowmesh.git
cd flowmesh

# 2. Configurer les variables d'environnement
cp .env.example .env

# 3. Lancer l'ensemble des services via Docker Compose
# Démarre : PostgreSQL 16, NATS JetStream, Redis 7, API Gateway, Web Console, Prometheus, Grafana
docker compose up -d

# 4. Charger le tenant de démonstration, les connecteurs et les workflows
python seed_demo.py
```

#### Accès aux Services & Identifiants

| Service | URL | Identifiants par défaut | Description |
| :--- | :--- | :--- | :--- |
| **Console Web** | `http://localhost:3000` | Pré-authentifié | Interface Next.js 15 d'administration |
| **Studio de Workflows** | `http://localhost:3000/workflows` | — | Concepteur visuel de DAGs et déclencheur |
| **Historique & IA d'Incident** | `http://localhost:3000/runs` | — | Visualiseur de traces et diagnostic d'incidents |
| **Connexions & Dérive** | `http://localhost:3000/connections` | — | Découverte de schéma et inspection de dérive |
| **Observabilité** | `http://localhost:3000/observability` | — | Tableau de bord télémétrique unifié |
| **Documentation Swagger API**| `http://localhost:8000/docs` | `bearer demo-token` | Explorateur d'API interactif OpenAPI |
| **Contrôle de Santé** | `http://localhost:8000/health` | Public | Sonde d'état du système |
| **Métriques Prometheus** | `http://localhost:8000/metrics` | Public | Cible de collecte OpenMetrics |
| **Grafana** | `http://localhost:3001` | `admin` / `admin` | Tableaux de bord de surveillance |

---

## Registres de Décision d'Architecture (ADRs)

- **[ADR-0001 : Architecture Exclusivement Sortante de l'Agent Edge](docs/adr/ADR-0001-agent-outbound-only.md)** — Zéro port ouvert sur les pare-feu clients.
- **[ADR-0002 : Rejet de Toute Exécution de Code Distant Arbitraire](docs/adr/ADR-0002-no-remote-code-execution.md)** — Signature obligatoire et connecteurs déclaratifs typés.
- **[ADR-0003 : Abstraction StateStore Générique pour Redis & RediForge](docs/adr/ADR-0003-statestore-abstraction.md)** — Verrous distribués et disjoncteurs atomiques.
- **[ADR-0004 : Gestion de Version Immuable des Workflows](docs/adr/ADR-0004-immutable-workflow-versions.md)** — Isolation stricte des exécutions et retour arrière immédiat.

---

## Licence

FlowMesh est un logiciel open-source distribué sous licence **Apache 2.0**.
Consultez le fichier [LICENSE](LICENSE) pour plus d'informations.
