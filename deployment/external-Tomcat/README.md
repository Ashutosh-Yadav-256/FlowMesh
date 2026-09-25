# FlowMesh Deployment: External Standalone Apache Tomcat 10.1 (WAR Packaging)

## Overview
For traditional enterprise IT shops operating centralized application server clusters, FlowMesh can be packaged as a **standard Web Application Archive (WAR)** and deployed into an external standalone **Apache Tomcat 10.1+** (Jakarta Servlet 6.0) instance.

## Architectural Changes for External Tomcat
1. **Servlet Initializer**: `EnterpriseWorkerApplication.java` extends `SpringBootServletInitializer` and overrides `configure(SpringApplicationBuilder application)`.
2. **Provided Scope**: The embedded Tomcat starter is scoped as `<provided>` via the `external-tomcat` Maven profile so that Tomcat's own runtime libraries take precedence.
3. **JNDI DataSource Configuration**: External Tomcat injects managed database connection pools via JNDI defined in `context.xml`.

## Step-by-Step Deployment Runbook

### Step 1: Build the WAR with Maven Profile
```bash
cd services/enterprise-worker
mvn clean package -Pexternal-tomcat -DskipTests
```
Output artifact: `target/flowmesh-enterprise-worker.war`

### Step 2: Configure Tomcat JNDI Resources (`context.xml`)
Copy `deployment/external-Tomcat/context.xml` into your Tomcat installation at `$CATALINA_BASE/conf/context.xml` or within the WAR at `META-INF/context.xml`.

### Step 3: Deploy to Tomcat webapps
```bash
cp target/flowmesh-enterprise-worker.war $CATALINA_HOME/webapps/flowmesh.war
$CATALINA_HOME/bin/startup.sh
```

### Step 4: Verify Deployment
Navigate to:
- Application Base: `http://localhost:8080/flowmesh/`
- Diagnostics API: `http://localhost:8080/flowmesh/api/v1/enterprise/deployment/info`
- Legacy AJAX Console: `http://localhost:8080/flowmesh/legacy-ajax-demo/index.html`

The deployment mode will report `EXTERNAL_TOMCAT_10`.
