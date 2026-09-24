package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/flowmesh/flowmesh/apps/agent/internal/agent"
	"github.com/flowmesh/flowmesh/apps/agent/internal/buffer"
	"github.com/flowmesh/flowmesh/apps/agent/internal/policy"
)

func main() {
	fmt.Println("==================================================")
	fmt.Println(" FlowMesh Edge Agent - Private Infrastructure Daemon")
	fmt.Println(" Zero Inbound Ports • Outbound mTLS • Pure-Go SQLite")
	fmt.Println("==================================================")

	idFlag := flag.String("id", "agent-prod-01", "Agent unique ID")
	tenantFlag := flag.String("tenant", "tenant_acme", "Customer Tenant ID")
	nameFlag := flag.String("name", "production-01", "Human-readable agent name")
	cpURLFlag := flag.String("control-plane-url", "http://localhost:8000", "FlowMesh Control Plane URL")
	tokenFlag := flag.String("token", "", "Zero-touch enrollment token")
	pubKeyFlag := flag.String("pubkey", "", "Control Plane Ed25519 Public Key (base64)")
	bufferPathFlag := flag.String("buffer-path", "", "Path to local SQLite buffer database")
	hbIntervalFlag := flag.Duration("heartbeat-interval", 5*time.Second, "Telemetry heartbeat interval")

	flag.Parse()

	bufPath := *bufferPathFlag
	if bufPath == "" {
		cwd, err := os.Getwd()
		if err != nil {
			cwd = "."
		}
		dataDir := filepath.Join(cwd, "data")
		_ = os.MkdirAll(dataDir, 0755)
		bufPath = filepath.Join(dataDir, "buffer.db")
	}

	buf, err := buffer.New(bufPath)
	if err != nil {
		log.Fatalf("Failed to initialize local SQLite buffer at %s: %v", bufPath, err)
	}
	defer buf.Close()
	log.Printf("Local SQLite offline buffer initialized at: %s", bufPath)

	pe := policy.NewEngine()
	pe.AddRule("postgres", "orders-db", policy.PolicyRule{
		AllowedOperations: []string{"read", "query"},
		AllowedResources:  []string{"orders", "customers", "order_items"},
		MaxLimit:          500,
	})
	pe.AddRule("rest", "warehouse-api", policy.PolicyRule{
		AllowedOperations: []string{"GET", "POST"},
		AllowedResources:  []string{"/shipments", "/inventory", "/shipments/*"},
		MaxLimit:          100,
	})
	log.Printf("Declarative policy engine configured with %d strict rules (deny by default)", pe.RuleCount())

	cfg := agent.Config{
		ID:                    *idFlag,
		TenantID:              *tenantFlag,
		Name:                  *nameFlag,
		Version:               "v0.5.0",
		ControlPlaneURL:       *cpURLFlag,
		EnrollmentToken:       *tokenFlag,
		ControlPlanePublicKey: *pubKeyFlag,
		HeartbeatInterval:     *hbIntervalFlag,
		PollInterval:          1 * time.Second,
		BufferPath:            bufPath,
	}

	ag := agent.New(cfg, pe, buf)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-sigChan
		fmt.Println("\nShutdown signal received. Terminating agent gracefully...")
		cancel()
	}()

	if *tokenFlag != "" {
		log.Printf("Initiating zero-touch enrollment with Control Plane...")
		if err := ag.Enroll(ctx); err != nil {
			log.Printf("Warning: Enrollment failed: %v (continuing with local config)", err)
		}
	}

	if err := ag.Start(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "Agent runtime error: %v\n", err)
		os.Exit(1)
	}
}
