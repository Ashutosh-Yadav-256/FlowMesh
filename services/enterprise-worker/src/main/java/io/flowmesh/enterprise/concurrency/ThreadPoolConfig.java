package io.flowmesh.enterprise.concurrency;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.lang.reflect.Method;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;

@Configuration
@EnableAsync
public class ThreadPoolConfig {

    private static final Logger log = LoggerFactory.getLogger(ThreadPoolConfig.class);

    @Bean(name = "reconciliationExecutor")
    @Primary
    public Executor reconciliationExecutor() {
        boolean useVirtualThreads = Boolean.parseBoolean(System.getProperty("flowmesh.threads.virtual", "false"));

        if (useVirtualThreads) {
            try {
                Method newVirtualThreadExecutorMethod = Executors.class.getMethod("newVirtualThreadPerTaskExecutor");
                ExecutorService virtualExecutor = (ExecutorService) newVirtualThreadExecutorMethod.invoke(null);
                log.info("Initialized Java Project Loom Virtual Thread Executor for Enterprise Worker");
                return virtualExecutor;
            } catch (Exception e) {
                log.warn("Virtual Threads requested but not supported by JVM. Falling back to bounded Platform ThreadPool.", e);
            }
        }

        int availableProcessors = Runtime.getRuntime().availableProcessors();
        int corePoolSize = Math.max(4, availableProcessors * 2);
        int maxPoolSize = Math.max(8, availableProcessors * 4);

        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(corePoolSize);
        executor.setMaxPoolSize(maxPoolSize);
        executor.setQueueCapacity(500);
        executor.setThreadNamePrefix("flowmesh-recon-");
        
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(30);
        executor.initialize();

        log.info("Initialized Bounded Platform ThreadPool: corePoolSize={}, maxPoolSize={}, queueCapacity={}",
                corePoolSize, maxPoolSize, 500);
        return executor;
    }

    @Bean(name = "batchWorkerExecutor")
    public Executor batchWorkerExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(8);
        executor.setMaxPoolSize(32);
        executor.setQueueCapacity(250);
        executor.setThreadNamePrefix("flowmesh-batch-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(20);
        executor.initialize();
        return executor;
    }
}
