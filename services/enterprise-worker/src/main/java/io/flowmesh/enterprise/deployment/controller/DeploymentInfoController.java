package io.flowmesh.enterprise.deployment.controller;

import jakarta.servlet.ServletContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/enterprise/deployment")
@CrossOrigin(origins = "*")
public class DeploymentInfoController {

    private final ServletContext servletContext;
    private final Environment environment;

    @Value("${server.port:8082}")
    private int serverPort;

    public DeploymentInfoController(
            @Autowired(required = false) ServletContext servletContext,
            Environment environment) {
        this.servletContext = servletContext;
        this.environment = environment;
    }

    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> getDeploymentInfo() {
        boolean isExternal = System.getProperty("catalina.base") != null;
        String mode = isExternal ? "EXTERNAL_TOMCAT" : "EMBEDDED_TOMCAT";

        Map<String, Object> info = new LinkedHashMap<>();
        info.put("deploymentMode", mode);
        info.put("serverEngine", servletContext != null ? servletContext.getServerInfo() : "Apache Tomcat/10.1.26");
        info.put("servletSpecification", "Jakarta Servlet 6.0");
        info.put("httpPort", serverPort);
        info.put("maxWorkerThreads", 200);
        info.put("minSpareThreads", 20);
        info.put("maxConnections", 8192);
        info.put("catalinaBase", System.getProperty("catalina.base", "N/A (Embedded In-Process)"));
        info.put("catalinaHome", System.getProperty("catalina.home", "N/A (Embedded In-Process)"));
        info.put("javaVersion", System.getProperty("java.version"));
        info.put("javaVendor", System.getProperty("java.vendor"));
        info.put("osName", System.getProperty("os.name"));
        info.put("activeProfiles", environment.getActiveProfiles().length > 0 ? environment.getActiveProfiles() : new String[]{"default"});

        return ResponseEntity.ok(info);
    }
}
