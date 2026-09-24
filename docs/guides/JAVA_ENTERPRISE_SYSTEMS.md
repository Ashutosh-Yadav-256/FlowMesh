# FlowMesh Enterprise - Java Concurrency, Memory Management & GC Architecture

This guide provides an exhaustive engineering and interview reference for the Java Enterprise Worker (`services/enterprise-worker`) within FlowMesh. It covers the **Java Memory Model (JMM)**, **Advanced Concurrency Patterns**, **JVM Runtime Architecture**, **Garbage Collection Algorithms**, and **Diagnostic Tooling**.

---

## 1. Executive Summary & FlowMesh Java Subsystem

The **FlowMesh Enterprise Worker** is a high-throughput, polyglot integration service built on **Spring Boot 3** and **Java 17/21 LTS**. It processes high-volume financial transactions, coordinates atomic multi-system ledger reconciliations, and connects with legacy ERPs (SAP, Oracle, Mainframes) and modern event streams (Apache Kafka, NATS JetStream).

```text
                  +----------------------------------------------+
                  |           INCOMING REST / KAFKA EVENT        |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |         MdcLoggingFilter (OncePerRequest)    |
                  |  - Injects X-Trace-ID & X-Tenant-ID to MDC   |
                  |  - Clears ThreadLocal MDC in finally block    |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |     LockFreeTokenBucketRateLimiter (CAS)     |
                  |  - AtomicLong state transition without locks |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |    TenantConcurrencyStripingManager (Locks)  |
                  |  - Striped partition execution per tenant    |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  | ConcurrentLedgerReconciliationService (Async)|
                  |  - CompletableFuture.supplyAsync() fan-out   |
                  |  - Bounded ThreadPool with CallerRunsPolicy  |
                  |  - Scatter-Gather parallel ledger RPCs       |
                  |  - CompletableFuture.allOf() fan-in          |
                  +----------------------------------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |         JvmDiagnosticsService / Actuator     |
                  |  - Real-time Heap, Non-Heap, GC, Thread stats|
                  +----------------------------------------------+
```

---

## 2. Java Concurrency Deep Dive

### 2.1 Platform Threads vs. Virtual Threads (Project Loom)

| Dimension | Platform Threads (OS Threads) | Virtual Threads (Java 21 Project Loom) |
| :--- | :--- | :--- |
| **Mapping** | 1:1 with Kernel OS threads | $M:N$ lightweight user-mode threads mounted on carrier OS threads |
| **Stack Size** | Reserved 1MB per thread (`-Xss1m`) | Dynamic footprint (starts at a few hundred bytes, grows in heap) |
| **Context Switching** | Expensive kernel context switch ($1-2\,\mu\text{s}$) | Inexpensive JVM continuation yield ($<10\,\text{ns}$) |
| **Maximum Capacity** | Typically 2,000–5,000 threads per JVM instance | Millions of concurrent threads |
| **Best Used For** | CPU-intensive mathematical / cryptographic hashing | I/O-bound blocking calls (DB queries, REST RPCs, Kafka consumers) |
| **FlowMesh Config** | `ThreadPoolConfig.reconciliationExecutor` | Enabled via `spring.threads.virtual.enabled=true` |

> **Gotcha in Virtual Threads:**
> Avoid *Thread Pinning*. A Virtual Thread becomes pinned to its carrier OS thread when executing within a `synchronized` block or calling a native method (`JNI`). In FlowMesh, we use `java.util.concurrent.locks.ReentrantLock` throughout `TenantConcurrencyStripingManager` instead of `synchronized` to ensure seamless unmounting and carrier thread reuse.

### 2.2 Java Memory Model (JMM) & Happens-Before Consistency

Under the **JSR-133 Java Memory Model**, modern multi-core processors use CPU caches (L1, L2, L3) and out-of-order execution pipelines. Without proper synchronization, writes by one thread may never become visible to other threads.

- **`volatile` Semantics**:
  1. **Visibility**: Guarantees that any write to a volatile field is immediately flushed to main memory and subsequent reads by any thread observe the latest value.
  2. **Ordering (Memory Barriers)**: Prevents instruction reordering around the volatile read/write using *LoadLoad*, *LoadStore*, *StoreStore*, and *StoreLoad* CPU fences.
  3. **No Atomicity**: `volatile int count++` is **not thread-safe** because it is a composite read-modify-write operation (`GETFIELD`, `IADD`, `PUTFIELD`).
- **Happens-Before Relationship**:
  - An unlock on a monitor *happens-before* every subsequent lock on that same monitor.
  - A write to a `volatile` variable *happens-before* every subsequent read of that same variable.
  - The call to `Thread.start()` *happens-before* any action in the started thread.
  - Completion of a task in `CompletableFuture` *happens-before* the execution of any chained callbacks (`thenApply`, `thenAccept`).

### 2.3 Lock-Free Concurrency & Hardware CAS Loops

In `LockFreeTokenBucketRateLimiter`, FlowMesh implements a lock-free token bucket algorithm using `AtomicLong`:

```java
while (true) {
    long current = availableTokens.get();
    if (current < tokensRequested) return false;
    long updated = current - tokensRequested;
    if (availableTokens.compareAndSet(current, updated)) {
        return true; // CAS succeeded atomically via CMPXCHG CPU instruction
    }
    // Contention detected: CAS failed because another thread updated the state; retry loop
}
```

- **CMPXCHG**: Compare-and-swap is a single CPU instruction executing atomically at the hardware memory bus or cache-coherency level (MESI protocol).
- **False Sharing & `LongAdder`**: When multiple threads update an `AtomicLong`, all CPU cores continuously invalidate the shared L1/L2 cache line (64 bytes). In `ConcurrentLedgerReconciliationService`, we use **`LongAdder`**, which internally maintains a cell array dynamically stripped per thread to eliminate cache-line bouncing.

### 2.4 Thread Pool Architecture & Backpressure Sizing

Thread pools in FlowMesh use bounded queues and deliberate rejection policies:

```text
ThreadPool Sizing Formula:
Optimal Thread Count = Number of Available CPUs * (1 + Wait Time / Service Time)

For FlowMesh I/O worker (Wait=40ms, Service=10ms, 8 CPUs):
Thread Count = 8 * (1 + 40/10) = 40 threads
```

- **Bounded Queue**: An `ArrayBlockingQueue(500)` prevents runaway heap consumption if downstream systems degrade.
- **`CallerRunsPolicy`**: When the queue fills, the thread submitting the task executes it directly. This slows down the ingress rate naturally, providing graceful, automatic backpressure without dropping transactions.
- **Graceful Termination**: `executor.setWaitForTasksToCompleteOnShutdown(true)` and `executor.setAwaitTerminationSeconds(30)` ensure in-flight transactions are committed before JVM termination.

### 2.5 Scatter-Gather Pattern with `CompletableFuture`

In `ConcurrentLedgerReconciliationService`:
1. **Fan-Out**: `transactions.stream().map(txn -> reconcileSingleTransactionAsync(...))` dispatches parallel asynchronous RPCs across external ledgers.
2. **Context Propagation**: The parent thread's MDC context (`traceId`, `tenantId`) is copied via `MDC.getCopyOfContextMap()` and set on the worker thread, ensuring end-to-end distributed tracing across thread hops.
3. **Non-Blocking Timeouts**: `.orTimeout(timeoutMs, TimeUnit.MILLISECONDS)` prevents hung connections from blocking worker threads indefinitely.
4. **Resilience**: `.exceptionally(...)` captures downstream timeouts or failures and produces a fallback `ReconciliationResult.failed(...)` rather than aborting the entire batch.
5. **Fan-In**: `CompletableFuture.allOf(...)` combines all futures into an aggregated `BatchReconciliationSummary`.

---

## 3. Java Memory Management & JVM Architecture

### 3.1 JVM Runtime Data Areas

```text
+-----------------------------------------------------------------------------------+
|                                  JVM RUNTIME MEMORY                               |
+-----------------------------------------------------------------------------------+
|  HEAP MEMORY (Shared across all threads)                                          |
|  +---------------------------------------------+-------------------------------+  |
|  |             YOUNG GENERATION                |        OLD / TENURED GEN      |  |
|  |  +----------------+--------+-------------+  |  +-------------------------+  |  |
|  |  |      EDEN      | S0     | S1          |  |  | Long-lived objects      |  |  |
|  |  | (TLAB Alloc)   | (From) | (To)        |  |  | Tenured after threshold |  |  |
|  |  +----------------+--------+-------------+  |  +-------------------------+  |  |
|  +---------------------------------------------+-------------------------------+  |
+-----------------------------------------------------------------------------------+
|  NON-HEAP & OFF-HEAP MEMORY (Native Process Memory)                                |
|  +---------------------+-----------------------+-------------------------------+  |
|  |      METASPACE      |      CODE CACHE       |     DIRECT BYTE BUFFERS       |  |
|  | Class metadata,     | JIT-compiled assembly | Netty & NIO socket buffers    |  |
|  | method bytecode     | machine instructions  | zero-copy I/O off-heap        |  |
|  +---------------------+-----------------------+-------------------------------+  |
+-----------------------------------------------------------------------------------+
|  THREAD-PRIVATE MEMORY (Allocated per thread)                                     |
|  +---------------------+-----------------------+-------------------------------+  |
|  |     JAVA STACK      |      PC REGISTERS     |       NATIVE METHOD STACK     |  |
|  | Stack frames, local | Bytecode instruction  | C/C++ JNI native call frames  |  |
|  | variables, operands | pointer               |                               |  |
|  +---------------------+-----------------------+-------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 3.2 Allocation & Lifecycle

1. **TLAB (Thread-Local Allocation Buffer)**: Each thread is allocated a dedicated sub-region of Eden space. New object allocations (`new EnterpriseTransaction(...)`) occur inside the thread's TLAB without taking global heap allocation locks.
2. **Escape Analysis**: If the JIT compiler determines an object does not escape the allocating method, it performs **Scalar Replacement** (allocating primitive fields directly on the execution stack or CPU registers, bypassing heap allocation entirely).
3. **Generational Hypothesis**: Most objects die young (temporary strings, request payloads, DTOs). Objects surviving multiple Minor GC cycles are promoted to the Old Generation once their age exceeds the MaxTenuringThreshold (default 15).

---

## 4. Garbage Collection (GC) Algorithms Compared

### 4.1 Production Garbage Collectors Comparison Matrix

| Collector | Memory Footprint | Max Pause Time SLA | Max Heap Scalability | Algorithm Details |
| :--- | :---: | :---: | :---: | :--- |
| **Serial GC** | Minimal | High ($>1\,\text{s}$) | $<100\,\text{MB}$ | Single-threaded stop-the-world. |
| **Parallel GC** | Low | Moderate ($200-500\,\text{ms}$) | Medium ($<4\,\text{GB}$) | Multi-threaded throughput collector. |
| **G1GC (Default)** | Moderate | **Configurable ($50-200\,\text{ms}$)** | **$4\,\text{GB} - 64\,\text{GB}$** | **Region-based, incremental, mixed collections.** |
| **ZGC / GenZGC** | Moderate-High | **Ultra-Low ($<1\,\text{ms}$)** | **$16\,\text{MB} - 16\,\text{TB}$** | **Colored pointers, load barriers, concurrent evacuation.** |
| **Shenandoah** | Moderate-High | Ultra-Low ($<5\,\text{ms}$)** | $4\,\text{GB} - 100\,\text{GB}$ | Brooks pointers / load-reference barriers. |

### 4.2 How G1GC Works (Production Profile A)

- **Heap Partitioning**: The heap is divided into approximately 2,048 equal-sized regions (from 1MB to 32MB depending on heap size). Regions are dynamically assigned as Eden, Survivor, or Old.
- **Humongous Objects**: Any object exceeding 50% of the G1 region size is categorized as a Humongous Object and allocated in contiguous sets of Humongous regions directly in the Old generation.
- **RSet (Remembered Sets)**: Each region maintains an RSet tracking references from other regions, allowing G1 to clean young regions without scanning the entire Old generation.
- **FlowMesh G1GC Tuning Flags**:
  ```bash
  -XX:+UseG1GC
  -XX:MaxGCPauseMillis=200
  -XX:InitiatingHeapOccupancyPercent=45
  -XX:G1ReservePercent=15
  -XX:G1HeapRegionSize=16m
  ```

### 4.3 How Generational ZGC Works (Production Profile B, Java 21+)

- **Colored Pointers**: Metadata about the object's GC state (Marked0, Marked1, Remapped) is encoded directly into reference pointer bits (64-bit addressing).
- **Load Barriers**: When application threads dereference an object pointer that is currently being relocated, a load barrier intercepts the read, redirects to the new location, and updates the pointer (self-healing pointers).
- **Zero Stop-the-World Evacuation**: Pause times stay below 1 millisecond regardless of whether the heap is 4GB or 4TB.

---

## 5. Five Classic Java Memory Leak Patterns & Solutions

### Pattern 1: `ThreadLocal` Leak in Thread Pools
- **Problem**: Thread pools (Tomcat worker threads, custom Executors) reuse long-lived threads. If a servlet or filter puts data into a `ThreadLocal` (e.g. SLF4J `MDC`) and fails to clear it, the object reference remains reachable indefinitely via `Thread.threadLocals`.
- **FlowMesh Solution**: In `MdcLoggingFilter.java`, `MDC.clear()` is strictly guaranteed in a `finally` block:
  ```java
  try {
      MDC.put("traceId", traceId);
      filterChain.doFilter(request, response);
  } finally {
      MDC.clear(); // Mandatory: prevents ThreadLocal memory leak
  }
  ```

### Pattern 2: Static Collection Unbounded Accumulation
- **Problem**: Storing items in `static Map<String, Object> cache = new HashMap<>()` without an eviction policy or size limit.
- **Solution**: Use Caffeine or Guava cache with `maximumSize(1000)` and `expireAfterWrite(10, TimeUnit.MINUTES)`, or a bounded ConcurrentHashMap with size gating.

### Pattern 3: Unclosed I/O Streams and JDBC Connections
- **Problem**: Leaving database connections, result sets, or network sockets open causes native file descriptor and memory exhaustion.
- **Solution**: Always use `try-with-resources` (`AutoCloseable`) and configure HikariCP with `leak-detection-threshold=15000` (15 seconds).

### Pattern 4: Improper `equals()` / `hashCode()` Implementation
- **Problem**: Modifying an object field used in `hashCode()` after inserting it into a `HashSet` or `HashMap` makes it impossible to retrieve or remove, permanently leaking the entry.
- **Solution**: Keep entity keys immutable or use database ID-based equals/hashCode with primary key stability.

### Pattern 5: Non-Static Inner Class Holding Outer Reference
- **Problem**: A non-static inner class holds an implicit hidden reference to the outer class instance (`OuterClass.this`), preventing the outer class from being garbage collected.
- **Solution**: Always declare inner classes as `static class` unless access to enclosing instance state is strictly required.

---

## 6. JVM Diagnostic & Troubleshooting Toolkit

| Scenario | Recommended Command / Tool | Purpose |
| :--- | :--- | :--- |
| **Inspect Live Heap Utilization** | `jcmd <pid> GC.heap_info` | Shows Eden, Survivor, Old Gen usage without triggering GC. |
| **Inspect Real-time GC Cycles** | `jstat -gcutil <pid> 1000` | Prints S0, S1, E, O, M percentages and YGC/FGC counts every second. |
| **Trigger Heap Dump on Demand** | `jmap -dump:live,format=b,file=heap.hprof <pid>` | Exports binary heap snapshot for Eclipse MAT or VisualVM analysis. |
| **Analyze Native Memory Leak** | `jcmd <pid> VM.native_memory detail` | Tracks Metaspace, C++ heap, and DirectByteBuffer memory growth. |
| **Diagnose Deadlock / Starvation** | `jcmd <pid> Thread.print` or `jstack -l <pid>` | Dumps thread stack traces and highlights locked/blocked monitors. |
| **Flamegraph CPU & Allocations** | `asprof -d 30 -e alloc -f alloc.html <pid>` | Async-profiler allocation flamegraph showing hot allocation sites. |
