package policy

import (
	"sync"
	"testing"
)

func TestNewEngine_EmptyRules(t *testing.T) {
	pe := NewEngine()
	if count := pe.RuleCount(); count != 0 {
		t.Fatalf("expected 0 rules in new engine, got %d", count)
	}
}

func TestAddAndGetRule(t *testing.T) {
	pe := NewEngine()
	rule := PolicyRule{
		AllowedOperations: []string{"read", "query"},
		AllowedResources:  []string{"orders"},
		MaxLimit:          100,
	}

	pe.AddRule("postgres", "conn-01", rule)

	if count := pe.RuleCount(); count != 1 {
		t.Fatalf("expected 1 rule, got %d", count)
	}

	got, found := pe.GetRule("postgres", "conn-01")
	if !found {
		t.Fatalf("expected rule to be found")
	}
	if got.MaxLimit != 100 {
		t.Fatalf("expected max limit 100, got %d", got.MaxLimit)
	}

	_, notFound := pe.GetRule("postgres", "non-existent")
	if notFound {
		t.Fatalf("expected non-existent rule to return false")
	}
}

func TestEvaluate_EmptyConnectorOrOperation(t *testing.T) {
	pe := NewEngine()

	cmd1 := Command{
		Operation: "query",
	}
	if err := pe.Evaluate(cmd1); err == nil {
		t.Fatalf("expected error for missing connector, but got nil")
	}

	cmd2 := Command{
		Connector: "postgres",
	}
	if err := pe.Evaluate(cmd2); err == nil {
		t.Fatalf("expected error for missing operation, but got nil")
	}
}

func TestEvaluate_DenyByDefault(t *testing.T) {
	pe := NewEngine()

	cmd := Command{
		Connector:    "postgres",
		ConnectionID: "unknown-db",
		Operation:    "read",
		Resource:     "users",
	}
	err := pe.Evaluate(cmd)
	if err == nil {
		t.Fatalf("expected deny by default for unregistered connection, but got nil")
	}
}

func TestEvaluate_AllowedOperation(t *testing.T) {
	pe := NewEngine()
	pe.AddRule("postgres", "orders-db", PolicyRule{
		AllowedOperations: []string{"READ", "query"},
		AllowedResources:  []string{"orders"},
		MaxLimit:          100,
	})

	cmd := Command{
		Connector:    "postgres",
		ConnectionID: "orders-db",
		Operation:    "read",
		Resource:     "orders",
		Limit:        10,
	}
	if err := pe.Evaluate(cmd); err != nil {
		t.Fatalf("expected operation 'read' to be permitted, got: %v", err)
	}
}

func TestEvaluate_ForbiddenOperation(t *testing.T) {
	pe := NewEngine()
	pe.AddRule("postgres", "orders-db", PolicyRule{
		AllowedOperations: []string{"read"},
		AllowedResources:  []string{"orders"},
	})

	cmd := Command{
		Connector:    "postgres",
		ConnectionID: "orders-db",
		Operation:    "delete",
		Resource:     "orders",
	}
	if err := pe.Evaluate(cmd); err == nil {
		t.Fatalf("expected forbidden operation 'delete' to fail, but it passed")
	}
}

func TestEvaluate_WildcardOperation(t *testing.T) {
	pe := NewEngine()
	pe.AddRule("rest", "external-api", PolicyRule{
		AllowedOperations: []string{"*"},
		AllowedResources:  []string{"*"},
	})

	cmd := Command{
		Connector:    "rest",
		ConnectionID: "external-api",
		Operation:    "custom-action",
		Resource:     "/anything",
	}
	if err := pe.Evaluate(cmd); err != nil {
		t.Fatalf("expected wildcard operation and resource to pass, got: %v", err)
	}
}

func TestEvaluate_PrefixWildcardResource(t *testing.T) {
	pe := NewEngine()
	pe.AddRule("s3", "blob-store", PolicyRule{
		AllowedOperations: []string{"read"},
		AllowedResources:  []string{"reports/*"},
	})

	validCmd := Command{
		Connector:    "s3",
		ConnectionID: "blob-store",
		Operation:    "read",
		Resource:     "reports/2026/q3.pdf",
	}
	if err := pe.Evaluate(validCmd); err != nil {
		t.Fatalf("expected prefix wildcard match to pass, got: %v", err)
	}

	invalidCmd := Command{
		Connector:    "s3",
		ConnectionID: "blob-store",
		Operation:    "read",
		Resource:     "secrets/passwords.txt",
	}
	if err := pe.Evaluate(invalidCmd); err == nil {
		t.Fatalf("expected resource outside prefix to fail, but it passed")
	}
}

func TestEvaluate_LimitExceeded(t *testing.T) {
	pe := NewEngine()
	pe.AddRule("postgres", "db", PolicyRule{
		AllowedOperations: []string{"query"},
		MaxLimit:          50,
	})

	cmd := Command{
		Connector:    "postgres",
		ConnectionID: "db",
		Operation:    "query",
		Limit:        100,
	}
	if err := pe.Evaluate(cmd); err == nil {
		t.Fatalf("expected limit 100 > maxLimit 50 to fail, but it passed")
	}
}

func TestConcurrentAccess(t *testing.T) {
	pe := NewEngine()
	pe.AddRule("postgres", "shared-db", PolicyRule{
		AllowedOperations: []string{"read", "query"},
		AllowedResources:  []string{"orders"},
		MaxLimit:          200,
	})

	var wg sync.WaitGroup
	numGoroutines := 50

	for i := 0; i < numGoroutines; i++ {
		wg.Add(2)

		go func(id int) {
			defer wg.Done()
			cmd := Command{
				Connector:    "postgres",
				ConnectionID: "shared-db",
				Operation:    "read",
				Resource:     "orders",
				Limit:        50,
			}
			_ = pe.Evaluate(cmd)
		}(i)

		go func(id int) {
			defer wg.Done()
			_ = pe.RuleCount()
			_, _ = pe.GetRule("postgres", "shared-db")
		}(i)
	}

	wg.Wait()
}
