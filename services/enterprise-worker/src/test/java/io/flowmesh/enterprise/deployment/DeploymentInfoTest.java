package io.flowmesh.enterprise.deployment;

import io.flowmesh.enterprise.deployment.controller.DeploymentInfoController;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.core.env.Environment;
import org.springframework.http.ResponseEntity;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("Tomcat Deployment Info & Configuration Tests")
class DeploymentInfoTest {

    @Test
    @DisplayName("Should report Tomcat deployment details")
    void testDeploymentInfo() {
        Environment mockEnv = Mockito.mock(Environment.class);
        Mockito.when(mockEnv.getActiveProfiles()).thenReturn(new String[]{"test"});

        DeploymentInfoController controller = new DeploymentInfoController(null, mockEnv);
        ResponseEntity<Map<String, Object>> response = controller.getDeploymentInfo();

        assertNotNull(response);
        assertEquals(200, response.getStatusCode().value());

        Map<String, Object> body = response.getBody();
        assertNotNull(body);
        assertTrue(body.containsKey("deploymentMode"));
        assertTrue(body.containsKey("serverEngine"));
        assertTrue(body.containsKey("servletSpecification"));
        assertEquals("Jakarta Servlet 6.0", body.get("servletSpecification"));
    }
}
