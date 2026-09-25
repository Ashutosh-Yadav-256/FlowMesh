# FlowMesh Web Console: React / Next.js 15 Enterprise Control Panel

## Overview
The **React Web Console** provides a modern, responsive web application for managing the FlowMesh ecosystem. Located at `apps/web/src/app/enterprise/page.tsx`, it connects directly to the Spring Boot Enterprise Worker (`services/enterprise-worker`) on port 8082.

## Key Capabilities
1. **Interactive Database Console**: Direct query execution, latency monitoring, and schema introspection across PostgreSQL, Oracle 23ai, and SQL Server 2022.
2. **Enterprise Messaging Hub**: Dispatches and monitors RabbitMQ AMQP messages and Jakarta JMS 3.1 queues and topics with real-time stream updates.
3. **Redis Cache & Distributed Locks**: Visualizes cache hit ratio, key-value browser, and interactive distributed lock coordinator.
4. **JMX MBean Monitoring**: Live polling of MBean attributes, remote invocation of JMX operations (`runHealthCheck()`, `triggerGarbageCollection()`, `evictAllCaches()`), and JVM memory gauges.
5. **Deployment Architecture**: Inspection of active Tomcat container (Embedded Tomcat 10.1 vs External Standalone Tomcat WAR), thread pool sizing, and connector statistics.
6. **Legacy AJAX Demo Integration**: Includes an embedded runner and direct launch capability for the legacy XMLHttpRequest console.

## Architecture
- **Framework**: Next.js 15 App Router / React 19
- **Styling**: Tailwind CSS with dark-mode first glassmorphism
- **Iconography**: Lucide React
- **API Communication**: Real-time asynchronous fetch with tenant header propagation (`X-Tenant-ID`)
