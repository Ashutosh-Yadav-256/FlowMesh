# FlowMesh Enterprise Monitoring: Java Management Extensions (JMX)

## Overview
FlowMesh exposes runtime control and telemetry via standard **JMX MBeans** registered with the JVM `PlatformMBeanServer`, accessible through JConsole, VisualVM, Prometheus JMX Exporter, and the Spring Boot REST API.

## Registered MBeans
### 1. `io.flowmesh:type=WorkerMonitor,name=CoreMonitor`
Interface: `FlowMeshWorkerMonitorMBean.java`
- **Managed Attributes**:
  - `ActiveTenantCount`: Number of isolated tenant partitions
  - `ProcessedTransactions`: Total transaction volume handled
  - `FailedTransactions`: Total failures
  - `AverageLatencyMs`: Rolling p95 processing duration
  - `CacheHitRatio`: Redis cache efficiency
  - `DatabaseActiveConnections`: Active connections in the primary pool
  - `RabbitMqDispatchedMessages`: AMQP dispatch count
  - `JmsSentMessages`: JMS message volume
  - `DeploymentMode`: Active runtime (`EMBEDDED_TOMCAT_10` vs `EXTERNAL_TOMCAT_10`)
  - `JvmUptime`: Time since container initialization
  - `FreeMemoryBytes` & `TotalMemoryBytes`: JVM heap telemetry
- **Managed Operations**:
  - `void resetCounters()`: Resets throughput and error metrics
  - `void evictAllCaches()`: Evicts all Redis and in-memory cache entries
  - `void triggerGarbageCollection()`: Calls `System.gc()` on demand
  - `String runHealthCheck()`: Pings all adapters, queues, and caches

## Connecting with VisualVM or JConsole
To connect remotely via JMX RMI:
```bash
java -Dcom.sun.management.jmxremote \
     -Dcom.sun.management.jmxremote.port=9010 \
     -Dcom.sun.management.jmxremote.local.only=false \
     -Dcom.sun.management.jmxremote.authenticate=false \
     -Dcom.sun.management.jmxremote.ssl=false \
     -jar target/enterprise-worker-2.4.0.jar
```

## Spring Boot REST API Reference
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/enterprise/monitoring/jmx/mbeans` | `GET` | Lists all MBeans registered in domain `io.flowmesh` |
| `/api/v1/enterprise/monitoring/jmx/attributes` | `GET` | Reads all attributes of `FlowMeshWorkerMonitor` |
| `/api/v1/enterprise/monitoring/jmx/operations/{operation}` | `POST` | Invokes an MBean operation (`runHealthCheck`, `triggerGarbageCollection`, `evictAllCaches`, `resetCounters`) |
| `/api/v1/enterprise/monitoring/jmx/jvm` | `GET` | Returns JVM Heap, Non-heap, Threading, and OS telemetry |
