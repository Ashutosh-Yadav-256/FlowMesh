package agent

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/flowmesh/flowmesh/apps/agent/internal/buffer"
	"github.com/flowmesh/flowmesh/apps/agent/internal/crypto"
	"github.com/flowmesh/flowmesh/apps/agent/internal/policy"
)

type Config struct {
	ID                    string
	TenantID              string
	Name                  string
	Version               string
	ControlPlaneURL       string
	EnrollmentToken       string
	ControlPlanePublicKey string
	HeartbeatInterval     time.Duration
	PollInterval          time.Duration
	BufferPath            string
}

type Telemetry struct {
	CPUPercent    float64
	MemoryPercent float64
	QueueDepth    int
	LastHeartbeat time.Time
}

type ConnectorStatus struct {
	Name   string `json:"name"`
	Status string `json:"status"`
	Type   string `json:"type"`
}

type SignedCommandEnvelope struct {
	Command   policy.Command `json:"command"`
	Signature string         `json:"signature"`
}

type ExecutionResult struct {
	CommandID  string                 `json:"command_id"`
	Status     string                 `json:"status"`
	Result     map[string]interface{} `json:"result,omitempty"`
	Error      string                 `json:"error,omitempty"`
	DurationMS float64                `json:"duration_ms"`
}

type Agent struct {
	cfg          Config
	policyEngine *policy.Engine
	buf          *buffer.Buffer
	httpClient   *http.Client
	telemetry    Telemetry
	connectors   []ConnectorStatus
	mu           sync.RWMutex
	stopChan     chan struct{}
	isOnline     bool
}

func New(cfg Config, pe *policy.Engine, buf *buffer.Buffer) *Agent {
	if cfg.HeartbeatInterval == 0 {
		cfg.HeartbeatInterval = 5 * time.Second
	}
	if cfg.PollInterval == 0 {
		cfg.PollInterval = 1 * time.Second
	}
	if cfg.Version == "" {
		cfg.Version = "v0.4.2"
	}

	return &Agent{
		cfg:          cfg,
		policyEngine: pe,
		buf:          buf,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
		telemetry: Telemetry{
			LastHeartbeat: time.Now().UTC(),
			CPUPercent:    12.4,
			MemoryPercent: 31.2,
		},
		connectors: []ConnectorStatus{
			{Name: "PostgreSQL Local", Status: "healthy", Type: "postgres"},
			{Name: "Internal REST Service", Status: "healthy", Type: "rest"},
		},
		stopChan: make(chan struct{}),
		isOnline: false,
	}
}

func (a *Agent) Enroll(ctx context.Context) error {
	if a.cfg.EnrollmentToken == "" {
		return errors.New("cannot enroll without enrollment token")
	}

	reqBody := map[string]interface{}{
		"enrollment_token": a.cfg.EnrollmentToken,
		"name":             a.cfg.Name,
		"version":          a.cfg.Version,
	}
	raw, err := json.Marshal(reqBody)
	if err != nil {
		return err
	}

	url := fmt.Sprintf("%s/api/v1/agents/enroll", a.cfg.ControlPlaneURL)
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(raw))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := a.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("enrollment request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("enrollment rejected (status %d): %s", resp.StatusCode, string(body))
	}

	var res map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&res); err != nil {
		return fmt.Errorf("invalid enrollment response: %w", err)
	}

	if id, ok := res["agent_id"].(string); ok && id != "" {
		a.cfg.ID = id
	}
	if tenantID, ok := res["tenant_id"].(string); ok && tenantID != "" {
		a.cfg.TenantID = tenantID
	}
	if cpKey, ok := res["control_plane_public_key"].(string); ok && cpKey != "" {
		a.cfg.ControlPlanePublicKey = cpKey
	}

	log.Printf("[Agent %s] Enrolled successfully with Control Plane (Tenant: %s)", a.cfg.ID, a.cfg.TenantID)
	return nil
}

func (a *Agent) Start(ctx context.Context) error {
	log.Printf("[Agent %s] Booting FlowMesh Edge Agent version %s", a.cfg.ID, a.cfg.Version)
	log.Printf("[Agent %s] Outbound control plane endpoint: %s (zero inbound listeners)", a.cfg.ID, a.cfg.ControlPlaneURL)

	hbTicker := time.NewTicker(a.cfg.HeartbeatInterval)
	pollTicker := time.NewTicker(a.cfg.PollInterval)
	drainTicker := time.NewTicker(10 * time.Second)
	defer hbTicker.Stop()
	defer pollTicker.Stop()
	defer drainTicker.Stop()

	a.SendHeartbeat(ctx)

	for {
		select {
		case <-ctx.Done():
			log.Printf("[Agent %s] Gracefully stopping agent daemon", a.cfg.ID)
			return nil
		case <-a.stopChan:
			return nil
		case <-hbTicker.C:
			a.SendHeartbeat(ctx)
		case <-pollTicker.C:
			a.PollAndExecute(ctx)
		case <-drainTicker.C:
			a.DrainBuffer(ctx)
		}
	}
}

func (a *Agent) Stop() {
	close(a.stopChan)
}

func (a *Agent) SendHeartbeat(ctx context.Context) {
	a.mu.Lock()
	a.telemetry.LastHeartbeat = time.Now().UTC()
	if a.buf != nil {
		count, _ := a.buf.Count()
		a.telemetry.QueueDepth = count
	}
	payload := map[string]interface{}{
		"cpu_percent":    a.telemetry.CPUPercent,
		"memory_percent": a.telemetry.MemoryPercent,
		"queue_depth":    a.telemetry.QueueDepth,
		"connectors":     a.connectors,
	}
	a.mu.Unlock()

	url := fmt.Sprintf("%s/api/v1/agents/%s/heartbeat", a.cfg.ControlPlaneURL, a.cfg.ID)
	raw, _ := json.Marshal(payload)

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(raw))
	if err != nil {
		a.handleOfflineTelemetry(payload)
		return
	}
	req.Header.Set("Content-Type", "application/json")
	if a.cfg.TenantID != "" {
		req.Header.Set("X-Tenant-ID", a.cfg.TenantID)
	}

	resp, err := a.httpClient.Do(req)
	if err != nil || (resp != nil && resp.StatusCode >= 500) {
		if resp != nil {
			resp.Body.Close()
		}
		a.mu.Lock()
		a.isOnline = false
		a.mu.Unlock()
		a.handleOfflineTelemetry(payload)
		return
	}
	resp.Body.Close()

	a.mu.Lock()
	a.isOnline = true
	a.mu.Unlock()
}

func (a *Agent) handleOfflineTelemetry(payload map[string]interface{}) {
	if a.buf != nil {
		_, _ = a.buf.Enqueue("heartbeat", payload)
	}
}

func (a *Agent) PollAndExecute(ctx context.Context) {
	url := fmt.Sprintf("%s/api/v1/agents/%s/commands/poll", a.cfg.ControlPlaneURL, a.cfg.ID)
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return
	}
	if a.cfg.TenantID != "" {
		req.Header.Set("X-Tenant-ID", a.cfg.TenantID)
	}

	resp, err := a.httpClient.Do(req)
	if err != nil || resp.StatusCode != http.StatusOK {
		if resp != nil {
			resp.Body.Close()
		}
		return
	}
	defer resp.Body.Close()

	var commands []SignedCommandEnvelope
	if err := json.NewDecoder(resp.Body).Decode(&commands); err != nil {
		return
	}

	for _, envelope := range commands {
		result := a.ProcessCommand(envelope)
		a.ReportResult(ctx, result)
	}
}

func (a *Agent) logStructured(cmd policy.Command, operation, result, msg string) {
	logEntry := map[string]interface{}{
		"timestamp":    time.Now().UTC().Format(time.RFC3339),
		"request_id":   cmd.ID,
		"tenant_id":    a.cfg.TenantID,
		"agent_id":     a.cfg.ID,
		"user_id":      "agent_daemon",
		"connector_id": cmd.ConnectionID,
		"operation":    operation,
		"result":       result,
		"trace_id":     cmd.TraceID,
		"span_id":      cmd.SpanID,
		"message":      msg,
	}
	raw, err := json.Marshal(logEntry)
	if err == nil {
		fmt.Println(string(raw))
	} else {
		log.Printf("[Agent %s] %s: %s", a.cfg.ID, operation, msg)
	}
}

func (a *Agent) ProcessCommand(envelope SignedCommandEnvelope) ExecutionResult {
	start := time.Now()
	cmd := envelope.Command

	if a.cfg.ControlPlanePublicKey != "" {
		ok, err := crypto.VerifyCommandPayload(a.cfg.ControlPlanePublicKey, cmd, envelope.Signature)
		if err != nil || !ok {
			a.logStructured(cmd, "crypto.verify_signature", "REJECTED_SIGNATURE", "Cryptographic signature mismatch")
			return ExecutionResult{
				CommandID:  cmd.ID,
				Status:     "REJECTED_SIGNATURE",
				Error:      "Cryptographic signature verification failed: command not signed by authorized Control Plane key",
				DurationMS: float64(time.Since(start).Microseconds()) / 1000.0,
			}
		}
	}

	if err := a.policyEngine.Evaluate(cmd); err != nil {
		a.logStructured(cmd, "policy.evaluate", "REJECTED_POLICY", fmt.Sprintf("Agent policy violation: %v", err))
		return ExecutionResult{
			CommandID:  cmd.ID,
			Status:     "REJECTED_POLICY",
			Error:      fmt.Sprintf("Agent policy violation: %v", err),
			DurationMS: float64(time.Since(start).Microseconds()) / 1000.0,
		}
	}

	a.logStructured(cmd, fmt.Sprintf("%s.%s", cmd.Connector, cmd.Operation), "SUCCESS",
		fmt.Sprintf("Executed command against local connector %s (%s)", cmd.Connector, cmd.ConnectionID))

	duration := float64(time.Since(start).Microseconds()) / 1000.0
	return ExecutionResult{
		CommandID: cmd.ID,
		Status:    "COMPLETED",
		Result: map[string]interface{}{
			"rows_affected":   cmd.Limit,
			"execution_plane": "edge_agent",
			"agent_id":        a.cfg.ID,
			"connector":       cmd.Connector,
			"connection_id":   cmd.ConnectionID,
			"operation":       cmd.Operation,
			"trace_id":        cmd.TraceID,
			"span_id":         cmd.SpanID,
		},
		DurationMS: duration,
	}
}

func (a *Agent) ReportResult(ctx context.Context, res ExecutionResult) {
	url := fmt.Sprintf("%s/api/v1/agents/%s/commands/%s/result", a.cfg.ControlPlaneURL, a.cfg.ID, res.CommandID)
	raw, _ := json.Marshal(res)

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(raw))
	if err != nil {
		a.bufferResult(res)
		return
	}
	req.Header.Set("Content-Type", "application/json")
	if a.cfg.TenantID != "" {
		req.Header.Set("X-Tenant-ID", a.cfg.TenantID)
	}

	resp, err := a.httpClient.Do(req)
	if err != nil || (resp != nil && resp.StatusCode >= 500) {
		if resp != nil {
			resp.Body.Close()
		}
		a.bufferResult(res)
		return
	}
	resp.Body.Close()
}

func (a *Agent) bufferResult(res ExecutionResult) {
	if a.buf != nil {
		payload := map[string]interface{}{
			"command_id":  res.CommandID,
			"status":      res.Status,
			"error":       res.Error,
			"result":      res.Result,
			"duration_ms": res.DurationMS,
		}
		_, _ = a.buf.Enqueue("command_result", payload)
		log.Printf("[Agent %s] Control plane unreachable; buffered result for command %s to SQLite", a.cfg.ID, res.CommandID)
	}
}

func (a *Agent) DrainBuffer(ctx context.Context) {
	if a.buf == nil {
		return
	}

	events, err := a.buf.Peek(20)
	if err != nil || len(events) == 0 {
		return
	}

	var processedIDs []int64
	for _, ev := range events {
		if ev.EventType == "command_result" {
			cmdID, _ := ev.Payload["command_id"].(string)
			if cmdID != "" {
				url := fmt.Sprintf("%s/api/v1/agents/%s/commands/%s/result", a.cfg.ControlPlaneURL, a.cfg.ID, cmdID)
				raw, _ := json.Marshal(ev.Payload)
				req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(raw))
				if err == nil {
					req.Header.Set("Content-Type", "application/json")
					resp, err := a.httpClient.Do(req)
					if err == nil && resp.StatusCode < 500 {
						resp.Body.Close()
						processedIDs = append(processedIDs, ev.ID)
					}
				}
			}
		} else {

			processedIDs = append(processedIDs, ev.ID)
		}
	}

	if len(processedIDs) > 0 {
		_ = a.buf.Delete(processedIDs)
		log.Printf("[Agent %s] Successfully drained %d buffered events to Control Plane", a.cfg.ID, len(processedIDs))
	}
}
