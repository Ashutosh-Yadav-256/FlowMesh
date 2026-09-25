# FlowMesh Deployment: Embedded Apache Tomcat 10.1

## Overview
By default, the FlowMesh Enterprise Worker packages **Embedded Apache Tomcat 10.1** inside a self-contained, executable "Fat JAR". This delivers cloud-native container portability while enforcing enterprise performance tuning.

## Performance Tuning Parameters
Configured in `application.yml` and programmatically via `TomcatDeploymentConfig.java`:

| Parameter | Setting | Description |
| :--- | :--- | :--- |
| `server.port` | `8082` | Default HTTP listener port |
| `server.tomcat.threads.max` | `200` | Maximum simultaneous request processing threads |
| `server.tomcat.threads.min-spare` | `20` | Always-allocated idle worker threads |
| `server.tomcat.max-connections` | `8192` | Operating system level concurrent socket connections |
| `server.tomcat.accept-count` | `100` | Inbound TCP SYN backlog queue |
| `server.tomcat.connection-timeout` | `20000ms` | Socket idle timeout before closing |
| `server.compression.enabled` | `true` | Gzip compression for JSON, XML, HTML, and JS payloads |

## Running with Embedded Tomcat
### Local Development
```bash
cd services/enterprise-worker
mvn spring-boot:run
```

### Production Fat JAR Execution
```bash
java -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -XX:+HeapDumpOnOutOfMemoryError \
     -jar target/enterprise-worker-2.4.0.jar
```
The application will boot and immediately listen on `http://localhost:8082` with Embedded Tomcat 10.
