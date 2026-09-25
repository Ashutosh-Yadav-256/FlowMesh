"use client";

import { useEffect, useState } from "react";
import {
  Server,
  Database,
  Radio,
  Layers,
  Cpu,
  Activity,
  Play,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Lock,
  Unlock,
  Send,
  Trash2,
  Terminal,
  Zap,
  Code2,
} from "lucide-react";
import { fetchFromWorker, postToWorker, getActiveTenantId } from "@/lib/api";

type TabType = "adapters" | "messaging" | "cache" | "jmx" | "deployment" | "apis" | "legacy";

export default function EnterpriseConsolePage() {
  const [activeTab, setActiveTab] = useState<TabType>("adapters");
  const [activeTenant, setActiveTenant] = useState("tenant_acme");
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Deployment & Telemetry State
  const [deployInfo, setDeployInfo] = useState<any>({
    deploymentMode: "EMBEDDED_TOMCAT_10",
    serverEngine: "Apache Tomcat/10.1.26",
    servletSpecification: "Jakarta Servlet 6.0",
    httpPort: 8082,
    maxWorkerThreads: 200,
    maxConnections: 8192,
    javaVersion: "17.0.18",
    activeProfiles: ["production"],
  });

  const [jmxAttrs, setJmxAttrs] = useState<any>({
    DeploymentMode: "EMBEDDED_TOMCAT_10",
    JvmUptime: "02h:14m:32s",
    ActiveTenantCount: 2,
    ProcessedTransactions: 1240,
    FailedTransactions: 3,
    AverageLatencyMs: 4.25,
    CacheHitRatio: 0.98,
    DatabaseActiveConnections: 5,
    RabbitMqDispatchedMessages: 42,
    JmsSentMessages: 18,
  });

  // DB Adapters State
  const [dbResults, setDbResults] = useState<any>({
    POSTGRESQL: { successful: true, latencyMs: 3, activePool: "FlowMeshEnterpriseHikariCP", databaseProduct: "PostgreSQL 16.4" },
    ORACLE: { successful: true, latencyMs: 12, activePool: "OracleUniversalConnectionPool", databaseProduct: "Oracle Database 23ai" },
    SQL_SERVER: { successful: true, latencyMs: 8, activePool: "FlowMeshMssqlPool", databaseProduct: "SQL Server 2022" },
  });
  const [selectedDbAdapter, setSelectedDbAdapter] = useState("POSTGRESQL");
  const [sqlQuery, setSqlQuery] = useState("SELECT 1 AS ping, CURRENT_TIMESTAMP AS server_time;");
  const [queryResult, setQueryResult] = useState<any>(null);
  const [introspectedTables, setIntrospectedTables] = useState<any[]>([]);

  // Messaging State
  const [rabbitStatus, setRabbitStatus] = useState<any>({
    totalPublished: 42,
    totalConsumed: 42,
    exchange: "flowmesh.direct",
    queue: "flowmesh.transactions.queue",
    dlq: "flowmesh.dlq",
  });
  const [jmsStatus, setJmsStatus] = useState<any>({
    totalSent: 18,
    totalReceived: 18,
    pointToPointQueue: "flowmesh.jms.queue",
    pubSubTopic: "flowmesh.jms.topic",
  });
  const [rabbitPayload, setRabbitPayload] = useState("Invoice #9901 Reconciliation Request");
  const [jmsPayload, setJmsPayload] = useState("General Ledger GL-401 Entry Batch");
  const [recentMessages, setRecentMessages] = useState<any[]>([]);

  // Redis Cache State
  const [cacheStats, setCacheStats] = useState<any>({
    hitRatio: 0.98,
    hitCount: 1420,
    missCount: 28,
    totalCachedKeys: 6,
  });
  const [cacheKey, setCacheKey] = useState("tenant:tenant_acme:policy");
  const [cacheVal, setCacheVal] = useState('{"rateLimit": 500, "region": "us-east-1"}');
  const [cacheTtl, setCacheTtl] = useState(300);
  const [cachedKeysList, setCachedKeysList] = useState<string[]>([]);
  const [lockResource, setLockResource] = useState("ledger-reconciliation");
  const [heldLockToken, setHeldLockToken] = useState("");

  // JMX Action message
  const [jmxActionResult, setJmxActionResult] = useState("");

  // Initial Load & Refresh
  useEffect(() => {
    setActiveTenant(getActiveTenantId());
    loadAllData();
  }, [refreshKey]);

  async function loadAllData() {
    setLoading(true);
    try {
      const dep = await fetchFromWorker("/api/v1/enterprise/deployment/info", deployInfo);
      setDeployInfo(dep);

      const jmx = await fetchFromWorker("/api/v1/enterprise/monitoring/jmx/attributes", jmxAttrs);
      setJmxAttrs(jmx);

      const dbs = await fetchFromWorker("/api/v1/enterprise/database/test-all", dbResults);
      setDbResults(dbs);

      const cStats = await fetchFromWorker("/api/v1/enterprise/cache/stats", cacheStats);
      setCacheStats(cStats);

      const keys = await fetchFromWorker<string[]>("/api/v1/enterprise/cache/keys", [
        "tenant:tenant_acme:config",
        "tenant:tenant_prod:config",
        "catalog:adapters:active",
      ]);
      setCachedKeysList(keys);

      const rStatus = await fetchFromWorker("/api/v1/enterprise/messaging/rabbitmq/status", rabbitStatus);
      setRabbitStatus(rStatus);

      const jStatus = await fetchFromWorker("/api/v1/enterprise/messaging/jms/status", jmsStatus);
      setJmsStatus(jStatus);
    } catch (e) {
      console.warn("Failed to load worker data:", e);
    } finally {
      setLoading(false);
    }
  }

  // Action Handlers
  async function handleTestDb(type: string) {
    setLoading(true);
    const res = await postToWorker(`/api/v1/enterprise/database/adapters/${type}/test`, {});
    if (res) {
      setDbResults((prev: any) => ({ ...prev, [type]: res }));
    }
    setLoading(false);
  }

  async function handleExecuteQuery() {
    setLoading(true);
    const res = await postToWorker(`/api/v1/enterprise/database/adapters/${selectedDbAdapter}/query`, {
      query: sqlQuery,
      parameters: [],
      timeoutSeconds: 15,
      maxRows: 50,
    });
    setQueryResult(res);
    setLoading(false);
  }

  async function handleIntrospectTables(type: string) {
    setLoading(true);
    const schema = type === "ORACLE" ? "FLOWMESH_ORCL" : type === "SQL_SERVER" ? "dbo" : "public";
    const res = await fetchFromWorker<any[]>(`/api/v1/enterprise/database/adapters/${type}/tables?schema=${schema}`, []);
    setIntrospectedTables(res);
    setLoading(false);
  }

  async function handlePublishRabbit() {
    const res = await postToWorker("/api/v1/enterprise/messaging/rabbitmq/publish", {
      tenantId: activeTenant,
      routingKey: "transaction.process",
      payload: { text: rabbitPayload, timestamp: new Date().toISOString() },
    });
    if (res) {
      setRecentMessages((prev) => [res, ...prev.slice(0, 15)]);
      setRabbitStatus((prev: any) => ({ ...prev, totalPublished: (prev.totalPublished || 0) + 1 }));
    }
  }

  async function handleSendJmsQueue() {
    const res = await postToWorker("/api/v1/enterprise/messaging/jms/queue/send", {
      tenantId: activeTenant,
      payload: { text: jmsPayload, action: "POINT_TO_POINT_QUEUE" },
    });
    if (res) {
      setRecentMessages((prev) => [res, ...prev.slice(0, 15)]);
      setJmsStatus((prev: any) => ({ ...prev, totalSent: (prev.totalSent || 0) + 1 }));
    }
  }

  async function handlePutCache() {
    await postToWorker("/api/v1/enterprise/cache/keys", {
      key: cacheKey,
      value: cacheVal,
      ttlSeconds: cacheTtl,
    });
    setCachedKeysList((prev) => Array.from(new Set([cacheKey, ...prev])));
    setCacheStats((prev: any) => ({ ...prev, totalCachedKeys: prev.totalCachedKeys + 1 }));
  }

  async function handleAcquireLock() {
    const res = await postToWorker<any>("/api/v1/enterprise/cache/lock/acquire", {
      tenantId: activeTenant,
      resource: lockResource,
      ttlMs: 30000,
    });
    if (res && res.acquired) {
      setHeldLockToken(res.token);
    } else {
      alert("Could not acquire lock: " + (res?.message || "Held by another node"));
    }
  }

  async function handleReleaseLock() {
    if (!heldLockToken) return;
    await postToWorker("/api/v1/enterprise/cache/lock/release", {
      tenantId: activeTenant,
      resource: lockResource,
      token: heldLockToken,
    });
    setHeldLockToken("");
  }

  async function handleInvokeJmx(op: string) {
    setLoading(true);
    const res = await postToWorker<any>(`/api/v1/enterprise/monitoring/jmx/operations/${op}`, {});
    if (res) {
      setJmxActionResult(`Invoked: ${op}() => ${JSON.stringify(res.result)}`);
      const updated = await fetchFromWorker("/api/v1/enterprise/monitoring/jmx/attributes", jmxAttrs);
      setJmxAttrs(updated);
    }
    setLoading(false);
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Top Hero Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
              Spring Boot 3.3.2
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300 border border-sky-300 dark:border-sky-700">
              {deployInfo.deploymentMode || "EMBEDDED_TOMCAT"}
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border border-amber-300 dark:border-amber-700">
              JMX: Active
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">Enterprise Worker Console</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            High-throughput integration backend: PostgreSQL, Oracle, SQL Server, Redis, RabbitMQ, JMS, and JMX telemetry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <a
            href="http://localhost:8082/legacy-ajax-demo/index.html"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-sky-600 text-white hover:bg-sky-700 transition"
          >
            <ExternalLink className="w-4 h-4" />
            Launch Legacy AJAX Console
          </a>
        </div>
      </div>

      {/* Quick Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="bg-white dark:bg-slate-900 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs text-slate-500">Processed Txns</span>
          <p className="text-lg font-bold text-slate-900 dark:text-white">{jmxAttrs.ProcessedTransactions ?? 1240}</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs text-slate-500">Avg Latency</span>
          <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">{jmxAttrs.AverageLatencyMs ?? 4.25} ms</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs text-slate-500">Cache Hit Ratio</span>
          <p className="text-lg font-bold text-sky-600 dark:text-sky-400">{Math.round((cacheStats.hitRatio || 0.98) * 100)}%</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs text-slate-500">RabbitMQ Queue</span>
          <p className="text-lg font-bold text-slate-900 dark:text-white">{rabbitStatus.totalPublished ?? 42} sent</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs text-slate-500">JMS Stream</span>
          <p className="text-lg font-bold text-slate-900 dark:text-white">{jmsStatus.totalSent ?? 18} sent</p>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
          <span className="text-xs text-slate-500">Tomcat Port</span>
          <p className="text-lg font-bold text-amber-600 dark:text-amber-400">:{deployInfo.httpPort || 8082}</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 overflow-x-auto space-x-1">
        {[
          { id: "adapters", label: "Database Adapters", icon: Database },
          { id: "messaging", label: "RabbitMQ & JMS", icon: Radio },
          { id: "cache", label: "Redis & Locks", icon: Zap },
          { id: "jmx", label: "JMX Monitoring", icon: Activity },
          { id: "deployment", label: "Tomcat Deployment", icon: Server },
          { id: "apis", label: "REST APIs Explorer", icon: Code2 },
          { id: "legacy", label: "Legacy AJAX Demo", icon: Terminal },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
                isActive
                  ? "border-sky-600 text-sky-600 dark:text-sky-400 dark:border-sky-400"
                  : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: Database Adapters */}
      {activeTab === "adapters" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* PostgreSQL */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  <h3 className="font-semibold text-slate-900 dark:text-white">PostgreSQL</h3>
                </div>
                <span className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-slate-600 dark:text-slate-400">
                  Primary Store
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-1">Product: {dbResults.POSTGRESQL?.databaseProduct || "PostgreSQL 16"}</p>
              <p className="text-xs text-slate-500 mb-1">Pool: {dbResults.POSTGRESQL?.activePool || "HikariCP"}</p>
              <p className="text-xs text-slate-500 mb-4">Latency: <span className="font-mono text-emerald-600 font-semibold">{dbResults.POSTGRESQL?.latencyMs ?? 3} ms</span></p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleTestDb("POSTGRESQL")}
                  className="flex-1 text-xs py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded font-medium transition"
                >
                  Test Ping
                </button>
                <button
                  onClick={() => { setSelectedDbAdapter("POSTGRESQL"); handleIntrospectTables("POSTGRESQL"); }}
                  className="flex-1 text-xs py-1.5 bg-sky-50 hover:bg-sky-100 dark:bg-sky-950/60 dark:hover:bg-sky-900/60 text-sky-700 dark:text-sky-300 rounded font-medium transition"
                >
                  Introspect
                </button>
              </div>
            </div>

            {/* Oracle */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                  <h3 className="font-semibold text-slate-900 dark:text-white">Oracle Database</h3>
                </div>
                <span className="text-xs bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded">
                  ERP Ledger
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-1">Product: {dbResults.ORACLE?.databaseProduct || "Oracle 23ai"}</p>
              <p className="text-xs text-slate-500 mb-1">Dialect: Dual / Pagination</p>
              <p className="text-xs text-slate-500 mb-4">Latency: <span className="font-mono text-amber-600 font-semibold">{dbResults.ORACLE?.latencyMs ?? 12} ms</span></p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleTestDb("ORACLE")}
                  className="flex-1 text-xs py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded font-medium transition"
                >
                  Test Ping
                </button>
                <button
                  onClick={() => { setSelectedDbAdapter("ORACLE"); handleIntrospectTables("ORACLE"); }}
                  className="flex-1 text-xs py-1.5 bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/60 dark:hover:bg-amber-900/60 text-amber-700 dark:text-amber-300 rounded font-medium transition"
                >
                  Introspect
                </button>
              </div>
            </div>

            {/* SQL Server */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span>
                  <h3 className="font-semibold text-slate-900 dark:text-white">SQL Server</h3>
                </div>
                <span className="text-xs bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-400 px-2 py-0.5 rounded">
                  Audit / T-SQL
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-1">Product: {dbResults.SQL_SERVER?.databaseProduct || "SQL Server 2022"}</p>
              <p className="text-xs text-slate-500 mb-1">Dialect: T-SQL TOP / sys.tables</p>
              <p className="text-xs text-slate-500 mb-4">Latency: <span className="font-mono text-sky-600 font-semibold">{dbResults.SQL_SERVER?.latencyMs ?? 8} ms</span></p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleTestDb("SQL_SERVER")}
                  className="flex-1 text-xs py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded font-medium transition"
                >
                  Test Ping
                </button>
                <button
                  onClick={() => { setSelectedDbAdapter("SQL_SERVER"); handleIntrospectTables("SQL_SERVER"); }}
                  className="flex-1 text-xs py-1.5 bg-sky-50 hover:bg-sky-100 dark:bg-sky-950/60 dark:hover:bg-sky-900/60 text-sky-700 dark:text-sky-300 rounded font-medium transition"
                >
                  Introspect
                </button>
              </div>
            </div>
          </div>

          {/* Interactive SQL Playground */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-sky-600" />
                  Interactive Enterprise SQL Playground
                </h3>
                <p className="text-xs text-slate-500">Execute parameterized queries directly against any enterprise adapter.</p>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={selectedDbAdapter}
                  onChange={(e) => setSelectedDbAdapter(e.target.value)}
                  className="px-3 py-1.5 text-xs bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md font-medium text-slate-800 dark:text-slate-200"
                >
                  <option value="POSTGRESQL">Target: PostgreSQL (Port 5432)</option>
                  <option value="ORACLE">Target: Oracle Database (Port 1521)</option>
                  <option value="SQL_SERVER">Target: SQL Server (Port 1433)</option>
                </select>
                <button
                  onClick={handleExecuteQuery}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-medium rounded-md transition"
                >
                  <Play className="w-3.5 h-3.5" />
                  Execute Query
                </button>
              </div>
            </div>

            <textarea
              value={sqlQuery}
              onChange={(e) => setSqlQuery(e.target.value)}
              rows={3}
              className="w-full p-3 font-mono text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-md focus:outline-none focus:ring-1 focus:ring-sky-500 text-slate-900 dark:text-slate-100"
              placeholder="Enter SQL statement..."
            />

            {/* Query Results Table */}
            {queryResult && (
              <div className="border border-slate-200 dark:border-slate-800 rounded-md overflow-hidden">
                <div className="bg-slate-100 dark:bg-slate-800/60 px-3 py-2 text-xs flex justify-between text-slate-600 dark:text-slate-300 font-mono">
                  <span>Status: {queryResult.status} | Rows: {queryResult.rowCount}</span>
                  <span>Execution: {queryResult.executionTimeMs} ms</span>
                </div>
                {queryResult.status === "ERROR" ? (
                  <div className="p-3 text-xs text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 font-mono">
                    {queryResult.errorMessage}
                  </div>
                ) : (
                  <div className="overflow-x-auto max-h-60">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-700">
                        <tr>
                          {queryResult.columnNames?.map((col: string, idx: number) => (
                            <th key={idx} className="p-2.5">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {queryResult.rows?.map((row: any, rIdx: number) => (
                          <tr key={rIdx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 font-mono text-[11px]">
                            {queryResult.columnNames?.map((col: string, cIdx: number) => (
                              <td key={cIdx} className="p-2.5 text-slate-800 dark:text-slate-200">
                                {row[col] !== undefined ? String(row[col]) : ""}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Introspected Schema View */}
            {introspectedTables.length > 0 && (
              <div className="mt-4 border border-slate-200 dark:border-slate-800 rounded-md p-4 bg-slate-50 dark:bg-slate-950/50">
                <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-200 mb-2">
                  Introspected Schema: {selectedDbAdapter} ({introspectedTables.length} Tables)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-56 overflow-y-auto">
                  {introspectedTables.map((tbl, i) => (
                    <div key={i} className="bg-white dark:bg-slate-900 p-2.5 rounded border border-slate-200 dark:border-slate-800 text-xs">
                      <div className="font-semibold text-sky-600 dark:text-sky-400">{tbl.tableName}</div>
                      <div className="text-[11px] text-slate-500">Schema: {tbl.tableSchema} · Type: {tbl.tableType}</div>
                      <div className="mt-1 text-[10px] text-slate-600 dark:text-slate-400 font-mono">
                        {tbl.columns?.map((c: any) => `${c.name}:${c.dataType}`).join(", ")}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: Messaging */}
      {activeTab === "messaging" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* RabbitMQ */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Radio className="w-5 h-5 text-emerald-600" />
                  <h3 className="font-semibold text-slate-900 dark:text-white">RabbitMQ (AMQP 0-9-1)</h3>
                </div>
                <span className="text-xs bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-medium px-2 py-0.5 rounded">
                  Exchange: {rabbitStatus.exchange}
                </span>
              </div>
              <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
                <p>Queue: <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">{rabbitStatus.queue}</code></p>
                <p>Dead-Letter Queue: <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">{rabbitStatus.dlq}</code></p>
                <p>Total Dispatches: <strong className="text-slate-900 dark:text-white font-mono">{rabbitStatus.totalPublished}</strong></p>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Publish Transaction Message:</label>
                <input
                  type="text"
                  value={rabbitPayload}
                  onChange={(e) => setRabbitPayload(e.target.value)}
                  className="w-full p-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded focus:ring-1 focus:ring-sky-500"
                />
                <button
                  onClick={handlePublishRabbit}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded transition"
                >
                  <Send className="w-3.5 h-3.5" /> Publish to RabbitMQ
                </button>
              </div>
            </div>

            {/* JMS */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Radio className="w-5 h-5 text-sky-600" />
                  <h3 className="font-semibold text-slate-900 dark:text-white">Jakarta JMS 3.1 (Artemis)</h3>
                </div>
                <span className="text-xs bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 font-medium px-2 py-0.5 rounded">
                  Embedded / External
                </span>
              </div>
              <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
                <p>Queue (P2P): <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">{jmsStatus.pointToPointQueue}</code></p>
                <p>Topic (Pub/Sub): <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">{jmsStatus.pubSubTopic}</code></p>
                <p>Messages Sent: <strong className="text-slate-900 dark:text-white font-mono">{jmsStatus.totalSent}</strong></p>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Dispatch JMS Message:</label>
                <input
                  type="text"
                  value={jmsPayload}
                  onChange={(e) => setJmsPayload(e.target.value)}
                  className="w-full p-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded focus:ring-1 focus:ring-sky-500"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSendJmsQueue}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-medium rounded transition"
                  >
                    <Send className="w-3.5 h-3.5" /> Send Queue (P2P)
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Messages Stream */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
            <h3 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider mb-3">
              Real-Time Dispatched Message Stream
            </h3>
            <div className="space-y-2 font-mono text-xs max-h-60 overflow-y-auto">
              {recentMessages.length === 0 ? (
                <p className="text-slate-500 text-xs italic">No messages dispatched yet in this session.</p>
              ) : (
                recentMessages.map((msg, idx) => (
                  <div key={idx} className="p-2.5 bg-slate-50 dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800">
                    <div className="flex justify-between text-slate-500 text-[11px] mb-1">
                      <span>[{msg.brokerType}] {msg.destination}</span>
                      <span>Tenant: {msg.tenantId}</span>
                    </div>
                    <div className="text-slate-800 dark:text-slate-200">{JSON.stringify(msg.payload)}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Redis Cache & Locks */}
      {activeTab === "cache" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Cache Key/Value Manager */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
              <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                Redis In-Memory Key Store
              </h3>
              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">Cache Key:</label>
                  <input
                    type="text"
                    value={cacheKey}
                    onChange={(e) => setCacheKey(e.target.value)}
                    className="w-full p-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">Value Payload:</label>
                  <input
                    type="text"
                    value={cacheVal}
                    onChange={(e) => setCacheVal(e.target.value)}
                    className="w-full p-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">TTL (Seconds):</label>
                  <input
                    type="number"
                    value={cacheTtl}
                    onChange={(e) => setCacheTtl(Number(e.target.value))}
                    className="w-32 p-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded font-mono"
                  />
                </div>
                <button
                  onClick={handlePutCache}
                  className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-medium transition"
                >
                  Store Key in Redis
                </button>
              </div>
            </div>

            {/* Distributed Lock Manager */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
              <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-500" />
                Distributed Lease / Mutual Exclusion (NX)
              </h3>
              <p className="text-xs text-slate-500">Atomic distributed leases guaranteeing tenant isolation.</p>
              <div className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">Resource Name:</label>
                  <input
                    type="text"
                    value={lockResource}
                    onChange={(e) => setLockResource(e.target.value)}
                    className="w-full p-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-medium mb-1">Active Lock Token:</label>
                  <input
                    type="text"
                    readOnly
                    value={heldLockToken || "(No lock currently acquired)"}
                    className="w-full p-2 bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded font-mono text-slate-600 dark:text-slate-400"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleAcquireLock}
                    disabled={!!heldLockToken}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded text-xs font-medium transition"
                  >
                    Acquire Lock (SET NX PX)
                  </button>
                  <button
                    onClick={handleReleaseLock}
                    disabled={!heldLockToken}
                    className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded text-xs font-medium transition"
                  >
                    Release Lock
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Active Keys Browser */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
            <h3 className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider mb-3">
              Active Cached Keys Explorer
            </h3>
            <div className="flex flex-wrap gap-2">
              {cachedKeysList.map((k, i) => (
                <span key={i} className="px-2.5 py-1 text-xs font-mono bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-sky-700 dark:text-sky-300">
                  {k}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: JMX Monitoring */}
      {activeTab === "jmx" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Managed Attributes Table */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
              <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-sky-500" />
                FlowMeshWorkerMonitor MBean Attributes
              </h3>
              <div className="border border-slate-200 dark:border-slate-800 rounded overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-700">
                    <tr><th className="p-2.5">Attribute Name</th><th className="p-2.5">Live MBean Value</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono text-[11px]">
                    <tr><td className="p-2.5">DeploymentMode</td><td className="p-2.5 font-semibold text-sky-600">{jmxAttrs.DeploymentMode}</td></tr>
                    <tr><td className="p-2.5">JvmUptime</td><td className="p-2.5">{jmxAttrs.JvmUptime}</td></tr>
                    <tr><td className="p-2.5">ActiveTenantCount</td><td className="p-2.5">{jmxAttrs.ActiveTenantCount}</td></tr>
                    <tr><td className="p-2.5">ProcessedTransactions</td><td className="p-2.5">{jmxAttrs.ProcessedTransactions}</td></tr>
                    <tr><td className="p-2.5">FailedTransactions</td><td className="p-2.5">{jmxAttrs.FailedTransactions}</td></tr>
                    <tr><td className="p-2.5">AverageLatencyMs</td><td className="p-2.5">{jmxAttrs.AverageLatencyMs} ms</td></tr>
                    <tr><td className="p-2.5">CacheHitRatio</td><td className="p-2.5">{Math.round((jmxAttrs.CacheHitRatio || 0.98) * 100)}%</td></tr>
                    <tr><td className="p-2.5">DatabaseActiveConnections</td><td className="p-2.5">{jmxAttrs.DatabaseActiveConnections}</td></tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* JMX Operations Executor */}
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
              <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-500" />
                Execute JMX Operations
              </h3>
              <p className="text-xs text-slate-500">Invoke remote lifecycle actions directly via the Platform MBeanServer.</p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleInvokeJmx("runHealthCheck")}
                  className="p-3 text-xs font-medium rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-left transition"
                >
                  <strong className="block text-slate-900 dark:text-white">runHealthCheck()</strong>
                  <span className="text-[11px] text-slate-500">Ping adapters &amp; queues</span>
                </button>
                <button
                  onClick={() => handleInvokeJmx("triggerGarbageCollection")}
                  className="p-3 text-xs font-medium rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-left transition"
                >
                  <strong className="block text-slate-900 dark:text-white">triggerGarbageCollection()</strong>
                  <span className="text-[11px] text-slate-500">Invoke System.gc()</span>
                </button>
                <button
                  onClick={() => handleInvokeJmx("evictAllCaches")}
                  className="p-3 text-xs font-medium rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-left transition"
                >
                  <strong className="block text-slate-900 dark:text-white">evictAllCaches()</strong>
                  <span className="text-[11px] text-slate-500">Clear Redis cache store</span>
                </button>
                <button
                  onClick={() => handleInvokeJmx("resetCounters")}
                  className="p-3 text-xs font-medium rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-left transition"
                >
                  <strong className="block text-slate-900 dark:text-white">resetCounters()</strong>
                  <span className="text-[11px] text-slate-500">Reset transaction counters</span>
                </button>
              </div>

              {jmxActionResult && (
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded font-mono text-xs text-emerald-800 dark:text-emerald-300">
                  {jmxActionResult}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: Tomcat Deployment */}
      {activeTab === "deployment" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
              <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Server className="w-4 h-4 text-sky-600" />
                Active Container Specification
              </h3>
              <ul className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                <li className="py-2.5 flex justify-between">
                  <span className="text-slate-500">Deployment Mode</span>
                  <strong className="font-mono text-sky-600">{deployInfo.deploymentMode}</strong>
                </li>
                <li className="py-2.5 flex justify-between">
                  <span className="text-slate-500">Servlet Engine</span>
                  <strong className="font-mono">{deployInfo.serverEngine}</strong>
                </li>
                <li className="py-2.5 flex justify-between">
                  <span className="text-slate-500">Servlet Spec Version</span>
                  <strong className="font-mono">{deployInfo.servletSpecification}</strong>
                </li>
                <li className="py-2.5 flex justify-between">
                  <span className="text-slate-500">Max Worker Threads</span>
                  <strong className="font-mono">{deployInfo.maxWorkerThreads}</strong>
                </li>
                <li className="py-2.5 flex justify-between">
                  <span className="text-slate-500">Max Keep-Alive Connections</span>
                  <strong className="font-mono">{deployInfo.maxConnections}</strong>
                </li>
                <li className="py-2.5 flex justify-between">
                  <span className="text-slate-500">Java Runtime</span>
                  <strong className="font-mono">{deployInfo.javaVersion}</strong>
                </li>
              </ul>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
              <h3 className="font-semibold text-slate-900 dark:text-white">Architecture: Embedded vs. External Tomcat</h3>
              <div className="border border-slate-200 dark:border-slate-800 rounded overflow-hidden text-xs">
                <table className="w-full text-left">
                  <thead className="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-700">
                    <tr><th className="p-2.5">Feature</th><th className="p-2.5">Embedded Tomcat</th><th className="p-2.5">External Tomcat (WAR)</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-[11px]">
                    <tr><td className="p-2.5 font-medium">Packaging</td><td className="p-2.5">Fat JAR (self-contained)</td><td className="p-2.5 font-mono">flowmesh-worker.war</td></tr>
                    <tr><td className="p-2.5 font-medium">Boot Mode</td><td className="p-2.5 font-mono">EnterpriseWorkerApplication.main()</td><td className="p-2.5 font-mono">SpringBootServletInitializer</td></tr>
                    <tr><td className="p-2.5 font-medium">Build Command</td><td className="p-2.5 font-mono">mvn package</td><td className="p-2.5 font-mono">mvn package -Pexternal-tomcat</td></tr>
                    <tr><td className="p-2.5 font-medium">Target Container</td><td className="p-2.5">Embedded Tomcat 10.1</td><td className="p-2.5">Tomcat 10.1+ / webapps/</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: REST APIs */}
      {activeTab === "apis" && (
        <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <Code2 className="w-4 h-4 text-sky-600" />
            Spring Boot 3 REST API Catalog
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {[
              { method: "GET", path: "/api/v1/enterprise/database/adapters", desc: "List all database adapters with pool telemetry" },
              { method: "POST", path: "/api/v1/enterprise/database/test-all", desc: "Execute connection tests on PostgreSQL, Oracle, SQL Server" },
              { method: "POST", path: "/api/v1/enterprise/database/adapters/{type}/query", desc: "Execute parameterized SQL statement" },
              { method: "POST", path: "/api/v1/enterprise/messaging/rabbitmq/publish", desc: "Publish AMQP transaction message" },
              { method: "POST", path: "/api/v1/enterprise/messaging/jms/queue/send", desc: "Send point-to-point Jakarta JMS message" },
              { method: "GET", path: "/api/v1/enterprise/cache/stats", desc: "Redis cache hit ratio & total cached keys" },
              { method: "POST", path: "/api/v1/enterprise/cache/lock/acquire", desc: "Acquire distributed NX lease for tenant" },
              { method: "GET", path: "/api/v1/enterprise/monitoring/jmx/attributes", desc: "Read live JMX WorkerMonitor attributes" },
              { method: "POST", path: "/api/v1/enterprise/monitoring/jmx/operations/{op}", desc: "Invoke JMX operation (GC, health, evict)" },
              { method: "GET", path: "/api/v1/enterprise/deployment/info", desc: "Embedded vs External Tomcat runtime status" },
            ].map((api, idx) => (
              <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800 font-mono">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${api.method === "GET" ? "bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-300" : "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300"}`}>
                    {api.method}
                  </span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{api.path}</span>
                </div>
                <div className="font-sans text-[11px] text-slate-500">{api.desc}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 7: Legacy AJAX Demo Embedded */}
      {activeTab === "legacy" && (
        <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Terminal className="w-4 h-4 text-sky-600" />
                Legacy AJAX Demonstration Console (Tomcat Served)
              </h3>
              <p className="text-xs text-slate-500">
                Pure JavaScript XMLHttpRequest Level 2 with state tracking, served directly from Spring Boot Tomcat.
              </p>
            </div>
            <a
              href="http://localhost:8082/legacy-ajax-demo/index.html"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 text-white rounded text-xs font-medium hover:bg-sky-700 transition"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Open in Dedicated Full Window
            </a>
          </div>

          <div className="border border-slate-200 dark:border-slate-800 rounded overflow-hidden h-[600px] bg-slate-900">
            <iframe
              src="http://localhost:8082/legacy-ajax-demo/index.html"
              className="w-full h-full border-none"
              title="Legacy AJAX Console"
            />
          </div>
        </div>
      )}
    </div>
  );
}
