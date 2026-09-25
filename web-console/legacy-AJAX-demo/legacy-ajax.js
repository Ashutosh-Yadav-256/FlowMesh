/**
 * FlowMesh Enterprise Worker - Legacy AJAX Administration Engine
 * Uses standard XMLHttpRequest (XHR) Level 2 with state transition tracking.
 */

// Base API URL (falls back to relative path if served on same host/port, or localhost:8082)
var API_BASE = window.location.port === "8082" ? "" : "http://localhost:8082";
var pollIntervalId = null;

// On DOM Loaded
document.addEventListener("DOMContentLoaded", function() {
    logAjax("DOM Loaded. Initializing Legacy AJAX Controller with target: " + (API_BASE || "Origin Host"));
    initConsole();
});

function initConsole() {
    updateTimestamp();
    fetchDeploymentInfo();
    pollAllTelemetry();

    var pollToggle = document.getElementById("poll-toggle");
    if (pollToggle) {
        pollToggle.addEventListener("change", function(e) {
            if (e.target.checked) {
                startAutoPoll();
            } else {
                stopAutoPoll();
            }
        });
    }
    startAutoPoll();
}

function updateTimestamp() {
    var tsEl = document.getElementById("current-timestamp");
    if (tsEl) {
        var now = new Date();
        tsEl.innerText = "System Time: " + now.toTimeString().split(" ")[0] + " (EST/UTC+5:30)";
    }
}

function startAutoPoll() {
    if (!pollIntervalId) {
        pollIntervalId = setInterval(function() {
            updateTimestamp();
            pollJmxAttributes();
        }, 3000);
        logAjax("Auto-polling timer registered: Interval = 3000ms");
    }
}

function stopAutoPoll() {
    if (pollIntervalId) {
        clearInterval(pollIntervalId);
        pollIntervalId = null;
        logAjax("Auto-polling timer paused.");
    }
}

/**
 * Core Legacy XMLHttpRequest Wrapper
 */
function ajaxRequest(method, path, payload, callback) {
    var xhr = new XMLHttpRequest();
    var url = API_BASE + path;
    var startTime = new Date().getTime();

    xhr.open(method, url, true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
    xhr.setRequestHeader("X-FlowMesh-Client", "Legacy-AJAX-Console-2.4.0");

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 1) {
            logAjax("[XHR 1/4: OPENED] " + method + " " + path);
        } else if (xhr.readyState === 2) {
            logAjax("[XHR 2/4: HEADERS_RECEIVED] Status: " + xhr.status + " " + xhr.statusText);
        } else if (xhr.readyState === 3) {
            logAjax("[XHR 3/4: LOADING] Receiving payload stream...");
        } else if (xhr.readyState === 4) {
            var elapsed = new Date().getTime() - startTime;
            if (xhr.status >= 200 && xhr.status < 300) {
                logAjax("[XHR 4/4: DONE 200 OK] " + method + " " + path + " (" + elapsed + "ms)");
                var responseData = null;
                try {
                    responseData = JSON.parse(xhr.responseText);
                } catch (e) {
                    responseData = xhr.responseText;
                }
                if (callback) callback(null, responseData);
            } else {
                logAjax("[XHR ERROR " + xhr.status + "] " + method + " " + path + " - " + xhr.responseText);
                if (callback) callback(new Error("HTTP " + xhr.status + ": " + xhr.statusText), null);
            }
        }
    };

    xhr.onerror = function(err) {
        logAjax("[XHR NETWORK_ERROR] Could not connect to " + url);
        if (callback) callback(err, null);
    };

    if (payload && (method === "POST" || method === "PUT")) {
        xhr.send(typeof payload === "string" ? payload : JSON.stringify(payload));
    } else {
        xhr.send();
    }
}

function logAjax(text) {
    var out = document.getElementById("ajax-log-output");
    if (out) {
        var time = new Date().toISOString().substring(11, 19);
        out.innerText = "[" + time + "] " + text + "\n" + out.innerText;
    }
}

function clearAjaxLog() {
    var out = document.getElementById("ajax-log-output");
    if (out) out.innerText = "Log cleared.";
}

/**
 * Tab Navigation
 */
function switchTab(tabId) {
    var panes = document.querySelectorAll(".tab-pane");
    panes.forEach(function(p) { p.classList.remove("active"); });

    var btns = document.querySelectorAll(".tab-btn");
    btns.forEach(function(b) { b.classList.remove("active"); });

    var targetPane = document.getElementById(tabId);
    if (targetPane) targetPane.classList.add("active");

    var currentBtn = event ? event.currentTarget : null;
    if (currentBtn) currentBtn.classList.add("active");

    logAjax("Navigated to tab: " + tabId);

    // Refresh context data on tab switch
    if (tabId === "tab-db") testAllDatabases();
    if (tabId === "tab-messaging") refreshMessagingStatus();
    if (tabId === "tab-redis") refreshRedisStats();
    if (tabId === "tab-jmx") pollJmxAttributes();
    if (tabId === "tab-deployment") fetchDeploymentInfo();
}

/**
 * TAB 1: Database Adapters
 */
function testAllDatabases() {
    ajaxRequest("POST", "/api/v1/enterprise/database/test-all", null, function(err, data) {
        if (err || !data) return;
        if (data.POSTGRESQL) {
            document.getElementById("pg-latency").innerText = data.POSTGRESQL.latencyMs + " ms";
            document.getElementById("pg-pool-info").innerText = data.POSTGRESQL.activePool + " (" + (data.POSTGRESQL.successful ? "ONLINE" : "OFFLINE") + ")";
        }
        if (data.ORACLE) {
            document.getElementById("orcl-latency").innerText = data.ORACLE.latencyMs + " ms";
            document.getElementById("orcl-pool-info").innerText = data.ORACLE.activePool + " (" + (data.ORACLE.successful ? "READY" : "OFFLINE") + ")";
        }
        if (data.SQL_SERVER) {
            document.getElementById("mssql-latency").innerText = data.SQL_SERVER.latencyMs + " ms";
            document.getElementById("mssql-pool-info").innerText = data.SQL_SERVER.activePool + " (" + (data.SQL_SERVER.successful ? "READY" : "OFFLINE") + ")";
        }
    });
}

function testDbConnection(type) {
    ajaxRequest("POST", "/api/v1/enterprise/database/adapters/" + type + "/test", null, function(err, data) {
        if (!err && data) {
            alert(type + " Connection Test:\nProduct: " + data.databaseProduct + "\nVersion: " + data.databaseVersion + "\nLatency: " + data.latencyMs + " ms\nMessage: " + data.message);
        }
    });
}

function introspectDb(type, schema) {
    ajaxRequest("GET", "/api/v1/enterprise/database/adapters/" + type + "/tables?schema=" + encodeURIComponent(schema), null, function(err, data) {
        if (!err && data) {
            renderTableGrid(data, type + " (" + schema + ")");
        }
    });
}

function executeCustomQuery() {
    var adapter = document.getElementById("query-adapter-select").value;
    var sql = document.getElementById("sql-query-input").value;
    if (!sql || !sql.trim()) {
        alert("Please enter a SQL statement.");
        return;
    }

    var payload = {
        query: sql,
        parameters: [],
        timeoutSeconds: 15,
        maxRows: 50
    };

    ajaxRequest("POST", "/api/v1/enterprise/database/adapters/" + adapter + "/query", payload, function(err, data) {
        if (!err && data) {
            renderQueryResult(data);
        }
    });
}

function renderTableGrid(tables, title) {
    var container = document.getElementById("query-result-table-container");
    if (!container) return;

    var html = "<div style='padding:10px;'><h4>Introspected Schema: " + title + " (" + tables.length + " Tables)</h4>";
    html += "<table class='data-table'><thead><tr><th>Table Name</th><th>Schema</th><th>Columns</th><th>Estimated Rows</th></tr></thead><tbody>";

    tables.forEach(function(t) {
        var cols = (t.columns || []).map(function(c) { return c.name + " (" + c.dataType + ")"; }).join(", ");
        html += "<tr><td><strong>" + t.tableName + "</strong></td><td>" + t.tableSchema + "</td><td><small>" + cols + "</small></td><td>" + (t.estimatedRowCount >= 0 ? t.estimatedRowCount : "Live Count") + "</td></tr>";
    });

    html += "</tbody></table></div>";
    container.innerHTML = html;
}

function renderQueryResult(res) {
    var container = document.getElementById("query-result-table-container");
    if (!container) return;

    var html = "<div style='padding:10px;'><h4>Query Result: " + res.databaseType + " (Execution Time: " + res.executionTimeMs + "ms, Rows: " + res.rowCount + ")</h4>";
    if (res.status === "ERROR") {
        html += "<div class='op-result-box' style='color:#b91c1c;'>Error: " + res.errorMessage + "</div>";
    } else {
        html += "<table class='data-table'><thead><tr>";
        (res.columnNames || []).forEach(function(col) {
            html += "<th>" + col + "</th>";
        });
        html += "</tr></thead><tbody>";

        (res.rows || []).forEach(function(row) {
            html += "<tr>";
            (res.columnNames || []).forEach(function(col) {
                html += "<td>" + (row[col] !== undefined ? row[col] : "") + "</td>";
            });
            html += "</tr>";
        });
        html += "</tbody></table>";
    }
    html += "</div>";
    container.innerHTML = html;
}

/**
 * TAB 2: Messaging
 */
function refreshMessagingStatus() {
    ajaxRequest("GET", "/api/v1/enterprise/messaging/rabbitmq/status", null, function(err, data) {
        if (!err && data) {
            document.getElementById("rabbit-count").innerText = data.totalPublished + " sent / " + data.totalConsumed + " recv";
        }
    });

    ajaxRequest("GET", "/api/v1/enterprise/messaging/jms/status", null, function(err, data) {
        if (!err && data) {
            document.getElementById("jms-count").innerText = data.totalSent + " sent / " + data.totalReceived + " recv";
        }
    });

    ajaxRequest("GET", "/api/v1/enterprise/messaging/rabbitmq/messages/recent", null, function(err, rData) {
        ajaxRequest("GET", "/api/v1/enterprise/messaging/jms/messages/recent", null, function(jErr, jData) {
            renderMessageStream(rData, jData);
        });
    });
}

function publishRabbitMessage() {
    var val = document.getElementById("rabbit-msg-input").value;
    var payload = {
        tenantId: "tenant_acme",
        routingKey: "transaction.process",
        payload: { text: val, timestamp: new Date().toISOString() }
    };
    ajaxRequest("POST", "/api/v1/enterprise/messaging/rabbitmq/publish", payload, function(err, res) {
        if (!err) {
            logAjax("Dispatched RabbitMQ message ID: " + res.messageId);
            refreshMessagingStatus();
        }
    });
}

function sendJmsQueueMessage() {
    var val = document.getElementById("jms-msg-input").value;
    var payload = {
        tenantId: "tenant_acme",
        payload: { action: "POINT_TO_POINT_QUEUE", content: val }
    };
    ajaxRequest("POST", "/api/v1/enterprise/messaging/jms/queue/send", payload, function(err, res) {
        if (!err) {
            logAjax("Dispatched JMS P2P Queue message ID: " + res.messageId);
            refreshMessagingStatus();
        }
    });
}

function publishJmsTopicMessage() {
    var val = document.getElementById("jms-msg-input").value;
    var payload = {
        tenantId: "tenant_prod",
        payload: { action: "PUB_SUB_TOPIC", content: val }
    };
    ajaxRequest("POST", "/api/v1/enterprise/messaging/jms/topic/publish", payload, function(err, res) {
        if (!err) {
            logAjax("Published JMS Topic message ID: " + res.messageId);
            refreshMessagingStatus();
        }
    });
}

function renderMessageStream(rabbitData, jmsData) {
    var container = document.getElementById("messaging-log-stream");
    if (!container) return;

    var html = "";
    var msgs = [];
    if (rabbitData && rabbitData.dispatched) msgs = msgs.concat(rabbitData.dispatched);
    if (jmsData && jmsData.sent) msgs = msgs.concat(jmsData.sent);

    if (msgs.length === 0) {
        container.innerText = "No messages currently in memory buffer.";
        return;
    }

    msgs.sort(function(a, b) { return new Date(b.timestamp) - new Date(a.timestamp); });

    msgs.forEach(function(m) {
        html += "<div style='margin-bottom:6px; padding-bottom:4px; border-bottom:1px dotted #334155;'>";
        html += "<strong>[" + m.brokerType + "]</strong> " + m.destination + " | Tenant: <code>" + m.tenantId + "</code> | MsgId: <code>" + m.messageId + "</code><br>";
        html += "<small style='color:#94a3b8;'>" + JSON.stringify(m.payload) + "</small>";
        html += "</div>";
    });

    container.innerHTML = html;
}

/**
 * TAB 3: Redis Cache & Distributed Locks
 */
function refreshRedisStats() {
    ajaxRequest("GET", "/api/v1/enterprise/cache/stats", null, function(err, data) {
        if (!err && data) {
            document.getElementById("redis-hit-ratio").innerText = Math.round(data.hitRatio * 100) + "%";
            document.getElementById("redis-hits").innerText = data.hitCount;
            document.getElementById("redis-misses").innerText = data.missCount;
            document.getElementById("redis-total-keys").innerText = data.totalCachedKeys;
        }
    });

    ajaxRequest("GET", "/api/v1/enterprise/cache/keys", null, function(err, keys) {
        if (!err && keys) {
            var container = document.getElementById("cache-keys-list");
            if (container) {
                container.innerHTML = keys.map(function(k) {
                    return "<span class='cache-tag'>" + k + "</span>";
                }).join(" ");
            }
        }
    });
}

function putCacheKey() {
    var k = document.getElementById("cache-key-input").value;
    var v = document.getElementById("cache-val-input").value;
    var ttl = parseInt(document.getElementById("cache-ttl-input").value, 10);

    ajaxRequest("POST", "/api/v1/enterprise/cache/keys", { key: k, value: v, ttlSeconds: ttl }, function(err, res) {
        if (!err) {
            logAjax("Successfully stored key in Redis: " + k);
            refreshRedisStats();
        }
    });
}

function acquireDistributedLock() {
    var tenant = document.getElementById("lock-tenant-input").value;
    var res = document.getElementById("lock-resource-input").value;

    ajaxRequest("POST", "/api/v1/enterprise/cache/lock/acquire", { tenantId: tenant, resource: res, ttlMs: 30000 }, function(err, data) {
        if (!err && data) {
            if (data.acquired) {
                document.getElementById("lock-token-display").value = data.token;
                alert("Distributed Lock Acquired!\nKey: " + data.lockKey + "\nToken: " + data.token);
            } else {
                alert("Could not acquire lock: " + data.message);
            }
        }
    });
}

function releaseDistributedLock() {
    var tenant = document.getElementById("lock-tenant-input").value;
    var res = document.getElementById("lock-resource-input").value;
    var token = document.getElementById("lock-token-display").value;

    if (!token) {
        alert("No lock token held currently.");
        return;
    }

    ajaxRequest("POST", "/api/v1/enterprise/cache/lock/release", { tenantId: tenant, resource: res, token: token }, function(err, data) {
        if (!err && data) {
            document.getElementById("lock-token-display").value = "";
            alert("Distributed Lock Released: " + (data.released ? "SUCCESS" : "FAILED / EXPIRED"));
        }
    });
}

/**
 * TAB 4: JMX Monitoring & Operations
 */
function pollJmxAttributes() {
    ajaxRequest("GET", "/api/v1/enterprise/monitoring/jmx/attributes", null, function(err, attrs) {
        if (err || !attrs) return;

        setEl("jmx-deploy-mode", attrs.DeploymentMode);
        setEl("jmx-uptime", attrs.JvmUptime);
        setEl("jmx-tenants", attrs.ActiveTenantCount);
        setEl("jmx-processed", attrs.ProcessedTransactions);
        setEl("jmx-failed", attrs.FailedTransactions);
        setEl("jmx-latency", attrs.AverageLatencyMs + " ms");
        setEl("jmx-cache-ratio", Math.round((attrs.CacheHitRatio || 0.98) * 100) + "%");
        setEl("jmx-db-conns", attrs.DatabaseActiveConnections);
        setEl("jmx-rabbit-msgs", attrs.RabbitMqDispatchedMessages);
        setEl("jmx-jms-msgs", attrs.JmsSentMessages);
    });
}

function invokeJmxOp(opName) {
    ajaxRequest("POST", "/api/v1/enterprise/monitoring/jmx/operations/" + opName, null, function(err, data) {
        var box = document.getElementById("jmx-op-result");
        if (box) {
            if (!err && data) {
                box.innerText = "Operation: " + data.operation + "() => Result: " + data.result;
                box.style.color = "#15803d";
            } else {
                box.innerText = "Operation failed: " + (err ? err.message : "unknown");
                box.style.color = "#b91c1c";
            }
        }
        pollJmxAttributes();
    });
}

/**
 * TAB 5: Deployment Info
 */
function fetchDeploymentInfo() {
    ajaxRequest("GET", "/api/v1/enterprise/deployment/info", null, function(err, data) {
        if (!err && data) {
            setEl("deploy-active-badge", data.deploymentMode);
            setEl("spec-engine", data.serverEngine);
            setEl("spec-servlet", data.servletSpecification);
            setEl("spec-port", data.httpPort);
            setEl("spec-threads", data.maxWorkerThreads);
            setEl("spec-conns", data.maxConnections);
            setEl("spec-java", data.javaVersion + " (" + data.javaVendor + ")");
            setEl("spec-base", data.catalinaBase);
        }
    });
}

function pollAllTelemetry() {
    updateTimestamp();
    testAllDatabases();
    refreshMessagingStatus();
    refreshRedisStats();
    pollJmxAttributes();
    fetchDeploymentInfo();
}

function setEl(id, val) {
    var el = document.getElementById(id);
    if (el && val !== undefined && val !== null) {
        el.innerText = val;
    }
}
