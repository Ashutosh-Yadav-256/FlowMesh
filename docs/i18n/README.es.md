# FlowMesh

<p align="center">
  <img src="https://img.shields.io/badge/Estado-Listo%20para%20Producción-00C853?style=for-the-badge&logo=statuspage&logoColor=white" alt="Production Ready" />
  <img src="https://img.shields.io/badge/Arquitectura-Nube%20Híbrida%20de%203%20Capas-007ACC?style=for-the-badge&logo=diagramsdotnet&logoColor=white" alt="3-Tier Architecture" />
  <img src="https://img.shields.io/badge/Licencia-Apache%202.0-blue?style=for-the-badge&logo=apache&logoColor=white" alt="Apache 2.0" />
</p>

<p align="center">
  <b> Idioma / Language / 语言 / 言語 / भाषा / Langue / 언어:</b><br>
  <a href="../../README.md">English</a> •
  <a href="./README.ja.md">日本語</a> •
  <a href="./README.zh.md">简体中文</a> •
  <a href="./README.hi.md">हिन्दी</a> •
  <a href="./README.fr.md">Français</a> •
  <a href="./README.ko.md">한국어</a> •
  <b>Español</b>
</p>

---

> **FlowMesh es una plataforma de código abierto, autohospedada e independiente de la nube para la integración empresarial y orquestación distribuida de flujos de trabajo.**
> Conecta bases de datos locales, ERPs heredados (SAP, Oracle), microservicios internos y APIs SaaS en flujos de trabajo DAG observables, tolerantes a fallos y reproducibles sin abrir puertos en los cortafuegos corporativos.

---

## Tabla de Contenidos

- [Resumen Ejecutivo](#-resumen-ejecutivo)
- [¿Por qué FlowMesh?](#-por-qué-flowmesh)
- [Capacidades Clave y Principios de Arquitectura](#-capacidades-clave-y-principios-de-arquitectura)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Estructura del Monorepositorio](#-estructura-del-monorepositorio)
- [Guía de Inicio Rápido](#-guía-de-inicio-rápido)
  - [Requisitos Previos](#requisitos-previos)
  - [Opción A: Pila Docker Compose de Producción (Recomendada)](#opción-a-pila-docker-compose-de-producción-recomendada)
  - [Opción B: Desarrollo Local Bare-Metal](#opción-b-desarrollo-local-bare-metal)
  - [Opción C: Despliegue en Kubernetes y Helm](#opción-c-despliegue-en-kubernetes-y-helm)
  - [Opción D: Despliegue del Agente Edge Seguro (Linux systemd)](#opción-d-despliegue-del-agente-edge-seguro-linux-systemd)
- [Módulos Funcionales Principales](#-módulos-funcionales-principales)
- [Observabilidad Distribuida y Telemetría](#-observabilidad-distribuida-y-telemetría)
- [Referencia del API Gateway](#-referencia-del-api-gateway)
- [Registros de Decisiones de Arquitectura (ADRs)](#-registros-de-decisiones-de-arquitectura-adrs)
- [Suite de Pruebas y Verificación Automatizada](#-suite-de-pruebas-y-verificación-automatizada)
- [Seguridad y Cumplimiento Normativo](#-seguridad-y-cumplimiento-normativo)
- [Contribución y Licencia](#-contribución-y-licencia)

---

## Resumen Ejecutivo

La infraestructura empresarial moderna se encuentra fragmentada entre ERPs heredados (SAP, Oracle), almacenes de datos en la nube, bases de datos relacionales (PostgreSQL, MySQL), intermediarios de mensajes y múltiples servicios SaaS externos. Las soluciones actuales imponen compromisos inaceptables:
1. **iPaaS SaaS Públicos** (Zapier, Workato, MuleSoft Cloud): Exigen enviar datos confidenciales y credenciales fuera de la red corporativa, violando regulaciones de soberanía de datos (GDPR, HIPAA, SOC 2).
2. **Middleware Empresarial Tradicional**: Licencias millonarias, dependencia técnica extrema y operaciones complejas.
3. **Scripts Internos y Tareas Cron**: Carentes de trazabilidad distribuida, detección de derivas en esquemas de datos y aislamiento multitenant.

**FlowMesh resuelve este dilema.** Construida sobre Python (FastAPI), Go, Next.js 15, NATS JetStream y PostgreSQL/Redis, ofrece una infraestructura de integración moderna y de alto rendimiento, 100% autohospedada y sin costes de licencia.

---

## ¿Por qué FlowMesh?

| Capacidad | FlowMesh | iPaaS Cloud SaaS | ESB Empresarial Tradicional | Scripts Propios Ad-Hoc |
| :--- | :---: | :---: | :---: | :---: |
| **Soberanía de Datos** | **100% Autohospedado** | Multi-tenant en Nube | En las instalaciones | Autohospedado |
| **Puertos de Entrada Cortafuegos**| **Cero (mTLS Saliente Únicamente)**| Requiere Puertos / Bastiones | VPNs Dedicadas Complejas | Variable |
| **Seguridad de Ejecución** | **Sin RCE Arbitrario (Firmado)** | Permite Ejecución Remota | Plugins JVM Pesados | Scripts sin auditoría |
| **Motor de Estado** | **Redis / RediForge / Memoria**| Caja Negra Propietaria | Cuello de botella en BD | Sin gestión de estado |
| **Observabilidad** | **W3C OpenTelemetry Nativo**| Solo Consola del Proveedor | Herramientas JMX Antiguas | Archivos de log simples |
| **Coste de Licencias** | **Gratuito (Apache 2.0)** | 50.000$ - 250.000$ / año | Contratos plurianuales caros | Alto coste de mantenimiento |

---

## Capacidades Clave y Principios de Arquitectura

- **Superficie de Ataque de Entrada Cero ([ADR-0001](docs/adr/ADR-0001-agent-outbound-only.md))**: Los agentes Edge de FlowMesh consultan el plano de control mediante túneles mTLS/WebSocket exclusivamente salientes. Los cortafuegos permanecen completamente sellados.
- **Acciones Estructuradas Criptográficamente Firmadas ([ADR-0002](docs/adr/ADR-0002-no-remote-code-execution.md))**: Eliminación de cualquier riesgo de Ejecución Remota de Código (RCE). Cada tarea ejecuta conectores declarativos verificados mediante firmas Ed25519 y listas blancas locales.
- **Abstracción StateStore Desacoplada ([ADR-0003](docs/adr/ADR-0003-statestore-abstraction.md))**: Compatibilidad con Redis, RediForge de ultra alto rendimiento y memoria local, con bloqueos distribuidos y disyuntores (circuit breakers) atómicos.
- **Versionado Inmutable de Flujos de Trabajo ([ADR-0004](docs/adr/ADR-0004-immutable-workflow-versions.md))**: Cada despliegue crea una versión $N+1$ inmutable. Las ejecuciones activas concluyen en su versión fijada; las reversiones (rollbacks) conmutan de inmediato al estado $N-1$ sin interrupción.
- **Cifrado de Envoltura (Envelope Encryption)**: Una clave maestra (KEK) descifra dinámicamente las claves de datos por inquilino (DEK) usando AES-256-GCM. Las credenciales nunca se almacenan en texto plano.
- **Aislamiento Multitenant a Nivel de Fila**: El patrón arquitectónico `TenantScopedRepository` impone el filtrado obligatorio por `tenant_id` en todas las transacciones de base de datos.
- **Mensajería de Alta Resiliencia**: NATS JetStream proporciona entrega garantizada al menos una vez, deduplicación estricta de mensajes, reintentos con retroceso exponencial y colas de descarte (Dead Letter Queues - DLQ).
- **Detección Automatizada de Deriva de Esquemas**: Identifica discrepancias estructurales en bases de datos clasificándolas en cambios compatibles (`WARNING`) o disruptivos (`CRITICAL`).

---

## Arquitectura del Sistema

```text
                                  FLOWMESH ARCHITECTURE
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
             PLANO DE CONTROL (PUERTO 8000)             MOTOR DE PLANO DE DATOS
               FastAPI / Python 3.12+                  Máquina de Estados de Flujo
          ├── 17 Enrutadores de Dominio              ├── Resolutor Topológico DAG
          ├── RBAC y Guardia de Autenticación        ├── Distribuidor de Tareas y Reintentos
          └── TenantScopedRepository                 └── Disyuntor y Colas DLQ
                       │                                         │
                       ├────────────────────┬────────────────────┤
                       ▼                    ▼                    ▼
                NATS JetStream        PostgreSQL 16         Redis / RediForge
              (Bus de Eventos)     (Sistema de Registro)    (StateStore y Bloqueos)
                       │                    │                    │
                       └────────────────────┼────────────────────┘
                                            │
                                    mTLS / Sondeo Saliente
                                     (Cero Puertos Entrantes)
                                            │
                       ┌────────────────────▼────────────────────┐
                       │          RED PRIVADA DEL CLIENTE / VPC  │
                       │                                         │
                       │             FLOWMESH AGENTE EDGE        │
                       │          (Demonio Estático en Go)       │
                       │  ├── Motor de Políticas Locales         │
                       │  ├── Búfer Local Desconectado SQLite    │
                       │  ├── Verificador de Firmas Ed25519      │
                       │  └── Ejecución Aislada de Conectores    │
                       │                                         │
                       │   ┌────────────┬───────────┬─────────┐  │
                       │   ▼            ▼           ▼         ▼  │
                       │ Postgres   APIs REST   Stripe/SAP  SFTP │
                       └─────────────────────────────────────────┘
```

Para especificaciones técnicas completas, consulte [ARCHITECTURE.es.md](./ARCHITECTURE.es.md).

---

## Guía de Inicio Rápido

### Requisitos Previos
- **Python**: `3.12+` (gestionado con `uv` o `pip`)
- **Node.js**: `20 LTS+` (gestor: `pnpm 9+`)
- **Go**: `1.23+` (requerido para compilar el agente Edge)
- **Docker**: `24+` y Compose `v2+`

### Opción A: Pila Docker Compose de Producción (Recomendada)

```bash
# 1. Clonar el repositorio
git clone https://github.com/your-org/flowmesh.git
cd flowmesh

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Iniciar todos los contenedores con Docker Compose
docker compose up -d

# 4. Inicializar inquilino demo, conectores y flujos de trabajo
python seed_demo.py
```

#### Servicios y Credenciales

| Servicio | URL | Credenciales por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| **Consola Web** | `http://localhost:3000` | Pre-autenticado | Interfaz de gestión Next.js 15 |
| **Estudio de Flujos** | `http://localhost:3000/workflows` | — | Diseñador visual de DAGs |
| **Historial e IA de Incidentes** | `http://localhost:3000/runs` | — | Trazas y diagnóstico de causas |
| **Conexiones y Deriva** | `http://localhost:3000/connections` | — | Descubrimiento de esquemas |
| **Observabilidad** | `http://localhost:3000/observability` | — | Métricas y telemetría |
| **Documentación Swagger** | `http://localhost:8000/docs` | `bearer demo-token` | Explorador interactivo OpenAPI |
| **Sonda de Salud** | `http://localhost:8000/health` | Público | Comprobación de liveness |
| **Métricas Prometheus** | `http://localhost:8000/metrics` | Público | Endpoint de scraping OpenMetrics |
| **Grafana** | `http://localhost:3001` | `admin` / `admin` | Paneles de monitorización |

---

## Registros de Decisiones de Arquitectura (ADRs)

- **[ADR-0001: Arquitectura Exclusivamente Saliente para el Agente Edge](docs/adr/ADR-0001-agent-outbound-only.md)** — Cero puertos abiertos en el cortafuegos.
- **[ADR-0002: Rechazo de Cualquier Ejecución Remota de Código](docs/adr/ADR-0002-no-remote-code-execution.md)** — Firmas criptográficas y conectores declarativos.
- **[ADR-0003: Abstracción StateStore Genérica para Redis y RediForge](docs/adr/ADR-0003-statestore-abstraction.md)** — Bloqueos distribuidos y disyuntores.
- **[ADR-0004: Versionado Inmutable de Flujos de Trabajo](docs/adr/ADR-0004-immutable-workflow-versions.md)** — Ejecución fijada y reversión inmediata.

---

## Licencia

FlowMesh es software de código abierto publicado bajo la licencia **Apache 2.0**.
Consulte [LICENSE](LICENSE) para más información.
