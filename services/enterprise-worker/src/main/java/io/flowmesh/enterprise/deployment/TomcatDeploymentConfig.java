package io.flowmesh.enterprise.deployment;

import org.apache.catalina.connector.Connector;
import org.apache.coyote.http11.AbstractHttp11Protocol;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class TomcatDeploymentConfig {

    private static final Logger log = LoggerFactory.getLogger(TomcatDeploymentConfig.class);

    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> tomcatCustomizer() {
        return factory -> {
            factory.addConnectorCustomizers((Connector connector) -> {
                if (connector.getProtocolHandler() instanceof AbstractHttp11Protocol<?> protocol) {
                    protocol.setMaxThreads(200);
                    protocol.setMinSpareThreads(20);
                    protocol.setMaxConnections(8192);
                    protocol.setAcceptCount(100);
                    protocol.setConnectionTimeout(20000);
                    protocol.setKeepAliveTimeout(15000);
                    protocol.setMaxKeepAliveRequests(100);
                    log.info("Embedded Tomcat 10 connector customized with high-concurrency enterprise settings");
                }
            });
        };
    }
}
