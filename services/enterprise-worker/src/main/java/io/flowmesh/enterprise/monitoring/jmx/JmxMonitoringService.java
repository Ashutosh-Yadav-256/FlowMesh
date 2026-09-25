package io.flowmesh.enterprise.monitoring.jmx;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.management.*;
import java.lang.management.ManagementFactory;
import java.util.*;

@Service
public class JmxMonitoringService {

    private static final Logger log = LoggerFactory.getLogger(JmxMonitoringService.class);

    private final MBeanServer mBeanServer = ManagementFactory.getPlatformMBeanServer();

    public List<Map<String, Object>> listMBeans(String domainFilter) {
        List<Map<String, Object>> list = new ArrayList<>();
        try {
            ObjectName pattern = (domainFilter != null && !domainFilter.isBlank())
                    ? new ObjectName(domainFilter + ":*")
                    : null;

            Set<ObjectName> names = mBeanServer.queryNames(pattern, null);
            for (ObjectName name : names) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("canonicalName", name.getCanonicalName());
                item.put("domain", name.getDomain());
                item.put("keyPropertyList", name.getKeyPropertyList());
                try {
                    MBeanInfo info = mBeanServer.getMBeanInfo(name);
                    item.put("className", info.getClassName());
                    item.put("description", info.getDescription());
                    item.put("attributeCount", info.getAttributes().length);
                    item.put("operationCount", info.getOperations().length);
                } catch (Exception ignored) {}
                list.add(item);
            }
        } catch (Exception e) {
            log.error("Failed to query JMX MBeans: {}", e.getMessage());
        }
        return list;
    }

    public Map<String, Object> getAttributes(String objectNameStr) {
        Map<String, Object> attrs = new LinkedHashMap<>();
        try {
            ObjectName name = new ObjectName(objectNameStr);
            MBeanInfo info = mBeanServer.getMBeanInfo(name);
            String[] attrNames = Arrays.stream(info.getAttributes())
                    .map(MBeanAttributeInfo::getName)
                    .toArray(String[]::new);

            AttributeList list = mBeanServer.getAttributes(name, attrNames);
            for (Attribute attr : list.asList()) {
                attrs.put(attr.getName(), attr.getValue());
            }
        } catch (Exception e) {
            log.error("Failed to read MBean attributes for '{}': {}", objectNameStr, e.getMessage());
            attrs.put("error", e.getMessage());
        }
        return attrs;
    }

    public Object invokeOperation(String objectNameStr, String operationName, Object[] params, String[] signature) {
        try {
            ObjectName name = new ObjectName(objectNameStr);
            return mBeanServer.invoke(name, operationName, params != null ? params : new Object[0],
                    signature != null ? signature : new String[0]);
        } catch (Exception e) {
            log.error("Failed to invoke JMX operation '{}' on '{}': {}", operationName, objectNameStr, e.getMessage());
            throw new RuntimeException("JMX invocation error: " + e.getMessage(), e);
        }
    }
}
