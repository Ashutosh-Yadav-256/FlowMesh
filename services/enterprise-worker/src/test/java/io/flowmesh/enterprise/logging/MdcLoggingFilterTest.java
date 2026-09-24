package io.flowmesh.enterprise.logging;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.MDC;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

@DisplayName("MDC Logging & Context Cleanup Unit Tests")
class MdcLoggingFilterTest {

    private MdcLoggingFilter filter;

    @BeforeEach
    void setUp() {
        filter = new MdcLoggingFilter();
        MDC.clear();
    }

    @Test
    @DisplayName("Should extract existing trace headers and inject into response")
    void testExtractsTraceHeaders() throws ServletException, IOException {
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader(MdcLoggingFilter.TRACE_ID_HEADER, "test-trace-123");
        request.addHeader(MdcLoggingFilter.CORRELATION_ID_HEADER, "test-corr-456");
        request.addHeader(MdcLoggingFilter.TENANT_ID_HEADER, "tenant-acme");
        request.setRemoteAddr("192.168.1.100");

        MockHttpServletResponse response = new MockHttpServletResponse();

        final String[] capturedMdcTrace = new String[1];
        final String[] capturedMdcTenant = new String[1];

        FilterChain filterChain = (req, res) -> {
            capturedMdcTrace[0] = MDC.get(MdcLoggingFilter.MDC_TRACE_ID);
            capturedMdcTenant[0] = MDC.get(MdcLoggingFilter.MDC_TENANT_ID);
        };

        filter.doFilter(request, response, filterChain);

        assertEquals("test-trace-123", capturedMdcTrace[0]);
        assertEquals("tenant-acme", capturedMdcTenant[0]);

        assertEquals("test-trace-123", response.getHeader(MdcLoggingFilter.TRACE_ID_HEADER));
        assertEquals("test-corr-456", response.getHeader(MdcLoggingFilter.CORRELATION_ID_HEADER));
        assertEquals("tenant-acme", response.getHeader(MdcLoggingFilter.TENANT_ID_HEADER));

        assertNull(MDC.get(MdcLoggingFilter.MDC_TRACE_ID), "MDC traceId must be cleared to prevent thread leak");
        assertNull(MDC.get(MdcLoggingFilter.MDC_TENANT_ID), "MDC tenantId must be cleared to prevent thread leak");
    }

    @Test
    @DisplayName("Should generate synthetic traceId if header is missing")
    void testGeneratesTraceIdWhenMissing() throws ServletException, IOException {
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        final String[] capturedMdcTrace = new String[1];

        filter.doFilter(request, response, (req, res) -> {
            capturedMdcTrace[0] = MDC.get(MdcLoggingFilter.MDC_TRACE_ID);
        });

        assertNotNull(capturedMdcTrace[0]);
        assertFalse(capturedMdcTrace[0].isEmpty());
        assertEquals(capturedMdcTrace[0], response.getHeader(MdcLoggingFilter.TRACE_ID_HEADER));

        assertNull(MDC.get(MdcLoggingFilter.MDC_TRACE_ID));
    }
}
