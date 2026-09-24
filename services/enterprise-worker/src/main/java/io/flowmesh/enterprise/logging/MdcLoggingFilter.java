package io.flowmesh.enterprise.logging;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class MdcLoggingFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(MdcLoggingFilter.class);

    public static final String TRACE_ID_HEADER = "X-Trace-ID";
    public static final String CORRELATION_ID_HEADER = "X-Correlation-ID";
    public static final String TENANT_ID_HEADER = "X-Tenant-ID";
    public static final String USER_ID_HEADER = "X-User-ID";

    public static final String MDC_TRACE_ID = "traceId";
    public static final String MDC_CORRELATION_ID = "correlationId";
    public static final String MDC_TENANT_ID = "tenantId";
    public static final String MDC_USER_ID = "userId";
    public static final String MDC_CLIENT_IP = "clientIp";

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        try {
            String traceId = request.getHeader(TRACE_ID_HEADER);
            if (!StringUtils.hasText(traceId)) {
                traceId = UUID.randomUUID().toString().replace("-", "");
            }

            String correlationId = request.getHeader(CORRELATION_ID_HEADER);
            if (!StringUtils.hasText(correlationId)) {
                correlationId = traceId;
            }

            String tenantId = request.getHeader(TENANT_ID_HEADER);
            if (!StringUtils.hasText(tenantId)) {
                tenantId = "system-default";
            }

            String userId = request.getHeader(USER_ID_HEADER);
            if (!StringUtils.hasText(userId)) {
                userId = "anonymous";
            }

            String clientIp = resolveClientIp(request);

            MDC.put(MDC_TRACE_ID, traceId);
            MDC.put(MDC_CORRELATION_ID, correlationId);
            MDC.put(MDC_TENANT_ID, tenantId);
            MDC.put(MDC_USER_ID, userId);
            MDC.put(MDC_CLIENT_IP, clientIp);

            response.setHeader(TRACE_ID_HEADER, traceId);
            response.setHeader(CORRELATION_ID_HEADER, correlationId);
            response.setHeader(TENANT_ID_HEADER, tenantId);

            filterChain.doFilter(request, response);

        } finally {
            MDC.clear();
        }
    }

    private String resolveClientIp(HttpServletRequest request) {
        String xForwardedFor = request.getHeader("X-Forwarded-For");
        if (StringUtils.hasText(xForwardedFor)) {
            return xForwardedFor.split(",")[0].trim();
        }
        return request.getRemoteAddr();
    }
}
