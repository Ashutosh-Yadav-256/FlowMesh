package io.flowmesh.enterprise.logging;

import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class LoggingAspect {

    private static final Logger log = LoggerFactory.getLogger(LoggingAspect.class);

    @Around("@annotation(logExecutionTime)")
    public Object logExecutionTime(ProceedingJoinPoint joinPoint, LogExecutionTime logExecutionTime) throws Throwable {
        long startNanos = System.nanoTime();
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        String className = signature.getDeclaringType().getSimpleName();
        String methodName = signature.getName();
        String operationName = logExecutionTime.operation().isEmpty() 
                ? className + "." + methodName 
                : logExecutionTime.operation();

        log.debug("START operation='{}'", operationName);

        try {
            Object result = joinPoint.proceed();
            long durationMillis = (System.nanoTime() - startNanos) / 1_000_000;

            if (durationMillis > logExecutionTime.thresholdMs()) {
                log.warn("SLA_BREACH operation='{}' latencyMs={} thresholdMs={} [SLOW_EXECUTION]",
                        operationName, durationMillis, logExecutionTime.thresholdMs());
            } else {
                log.info("COMPLETE operation='{}' latencyMs={}", operationName, durationMillis);
            }

            return result;
        } catch (Throwable ex) {
            long durationMillis = (System.nanoTime() - startNanos) / 1_000_000;
            log.error("FAILED operation='{}' latencyMs={} exception='{}' message='{}'",
                    operationName, durationMillis, ex.getClass().getSimpleName(), ex.getMessage(), ex);
            throw ex;
        }
    }
}
