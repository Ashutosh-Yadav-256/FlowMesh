package io.flowmesh.enterprise.monitoring;

import io.flowmesh.enterprise.adapters.db.DatabaseAdapterRegistry;
import io.flowmesh.enterprise.adapters.db.OracleDatabaseAdapter;
import io.flowmesh.enterprise.adapters.db.SqlServerDatabaseAdapter;
import io.flowmesh.enterprise.messaging.jms.JmsMessageProducer;
import io.flowmesh.enterprise.messaging.rabbitmq.RabbitMqProducer;
import io.flowmesh.enterprise.monitoring.jmx.FlowMeshWorkerMonitor;
import io.flowmesh.enterprise.monitoring.jmx.JmxMonitoringService;
import io.flowmesh.enterprise.redis.RedisCacheService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("JMX Monitoring & MBean Telemetry Tests")
class JmxMonitoringTest {

    private FlowMeshWorkerMonitor workerMonitor;
    private JmxMonitoringService jmxService;

    @BeforeEach
    void setUp() {
        DatabaseAdapterRegistry registry = new DatabaseAdapterRegistry(List.of(
                new OracleDatabaseAdapter(),
                new SqlServerDatabaseAdapter()
        ));
        RedisCacheService cacheService = new RedisCacheService(null);
        RabbitMqProducer rabbitProducer = new RabbitMqProducer(null);
        JmsMessageProducer jmsProducer = new JmsMessageProducer(null);

        workerMonitor = new FlowMeshWorkerMonitor(registry, cacheService, rabbitProducer, jmsProducer);
        workerMonitor.registerMBean();

        jmxService = new JmxMonitoringService();
    }

    @Test
    @DisplayName("Worker monitor should expose valid MBean attributes")
    void testMBeanAttributes() {
        assertTrue(workerMonitor.getActiveTenantCount() > 0);
        assertTrue(workerMonitor.getProcessedTransactions() >= 0);
        assertTrue(workerMonitor.getAverageLatencyMs() > 0);
        assertNotNull(workerMonitor.getDeploymentMode());
        assertNotNull(workerMonitor.getJvmUptime());
        assertTrue(workerMonitor.getTotalMemoryBytes() > 0);
    }

    @Test
    @DisplayName("JMX operations should execute cleanly")
    void testMBeanOperations() {
        String health = workerMonitor.runHealthCheck();
        assertNotNull(health);
        assertTrue(health.contains("HEALTH_OK"));

        workerMonitor.recordSuccess();
        workerMonitor.resetCounters();
        assertEquals(0, workerMonitor.getProcessedTransactions());

        assertDoesNotThrow(() -> workerMonitor.triggerGarbageCollection());
        assertDoesNotThrow(() -> workerMonitor.evictAllCaches());
    }

    @Test
    @DisplayName("JMX service should query registered MBeans in JVM")
    void testJmxServiceDiscovery() {
        List<Map<String, Object>> mbeans = jmxService.listMBeans("io.flowmesh");
        assertFalse(mbeans.isEmpty());

        Map<String, Object> attrs = jmxService.getAttributes(FlowMeshWorkerMonitor.MBEAN_NAME);
        assertNotNull(attrs);
        assertTrue(attrs.containsKey("ActiveTenantCount"));
        assertTrue(attrs.containsKey("DeploymentMode"));
    }
}
