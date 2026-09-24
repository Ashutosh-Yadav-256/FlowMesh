Feature: Enterprise Multi-Tenant Workflow Orchestration
  As an enterprise systems architect
  I want to orchestrate cross-platform transactions across heterogeneous databases and queues
  So that business processes run with zero data loss and strict tenant isolation

  Background:
    Given the FlowMesh control plane is operational
    And tenant "acme-corp" is authenticated with enterprise credentials

  @smoke @enterprise
  Scenario: End-to-end database replication from PostgreSQL to Oracle
    Given an active PostgreSQL source connector "pg_orders_db"
    And an active Oracle ERP target connector "oracle_ledger_db"
    When an event "order.placed" is published to the event bus
    Then the workflow engine triggers DAG "ReplicateOrderToLedger"
    And step "transform_payload" executes successfully within 200 milliseconds
    And step "insert_oracle_ledger" commits the transaction to Oracle
    And an immutable audit log is recorded with status "COMPLETED"

  @security @compliance
  Scenario: Strict tenant isolation during concurrent workflow executions
    Given tenant "acme-corp" initiates workflow "AcmePayroll"
    And tenant "globex-corp" initiates workflow "GlobexInvoicing"
    When both workflows execute simultaneously
    Then tenant "acme-corp" execution data must not be accessible to "globex-corp"
    And the state store partitions leases by tenant ID
    And no cross-tenant memory or cryptographic key leakage occurs

  @resilience @messaging
  Scenario: Graceful event buffering during downstream message queue degradation
    Given the IBM MQ connector "ibmmq_settlement" has its circuit breaker OPEN
    When incoming events are dispatched to "PAYMENT.SETTLEMENT.QUEUE"
    Then the event bus diverts the messages to the Dead Letter Queue
    And an incident is created in the incident manager with severity "P2"
    And zero message payloads are lost
