package policy

import (
	"errors"
	"fmt"
	"strings"
	"sync"
)

type Command struct {
	ID           string                 `json:"id"`
	Type         string                 `json:"type"`
	Connector    string                 `json:"connector"`
	ConnectionID string                 `json:"connection_id"`
	Operation    string                 `json:"operation"`
	Resource     string                 `json:"resource"`
	Limit        int                    `json:"limit,omitempty"`
	Payload      map[string]interface{} `json:"payload"`
	TraceID      string                 `json:"trace_id,omitempty"`
	SpanID       string                 `json:"span_id,omitempty"`
}

type PolicyRule struct {
	AllowedOperations []string `yaml:"allowed_operations" json:"allowed_operations"`
	AllowedResources  []string `yaml:"allowed_resources" json:"allowed_resources"`
	MaxLimit          int      `yaml:"max_limit" json:"max_limit"`
}

type Engine struct {
	mu    sync.RWMutex
	rules map[string]PolicyRule
}

func NewEngine() *Engine {
	return &Engine{
		rules: make(map[string]PolicyRule),
	}
}

func (e *Engine) AddRule(connector, connectionID string, rule PolicyRule) {
	e.mu.Lock()
	defer e.mu.Unlock()
	key := fmt.Sprintf("%s:%s", connector, connectionID)
	e.rules[key] = rule
}

func (e *Engine) GetRule(connector, connectionID string) (PolicyRule, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	key := fmt.Sprintf("%s:%s", connector, connectionID)
	rule, found := e.rules[key]
	return rule, found
}

func (e *Engine) RuleCount() int {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return len(e.rules)
}

func (e *Engine) Evaluate(cmd Command) error {
	e.mu.RLock()
	defer e.mu.RUnlock()

	if cmd.Connector == "" || cmd.Operation == "" {
		return errors.New("policy violation: missing connector or operation")
	}

	key := fmt.Sprintf("%s:%s", cmd.Connector, cmd.ConnectionID)
	rule, found := e.rules[key]
	if !found {
		return fmt.Errorf("policy violation: connection '%s' on connector '%s' is NOT allowlisted (deny by default)", cmd.ConnectionID, cmd.Connector)
	}

	opAllowed := false
	for _, op := range rule.AllowedOperations {
		if strings.EqualFold(op, cmd.Operation) || op == "*" {
			opAllowed = true
			break
		}
	}
	if !opAllowed {
		return fmt.Errorf("policy violation: operation '%s' is forbidden on connection '%s'", cmd.Operation, cmd.ConnectionID)
	}

	if cmd.Resource != "" && len(rule.AllowedResources) > 0 {
		resAllowed := false
		for _, res := range rule.AllowedResources {
			if strings.EqualFold(res, cmd.Resource) || res == "*" {
				resAllowed = true
				break
			}

			if strings.HasSuffix(res, "*") && strings.HasPrefix(cmd.Resource, strings.TrimSuffix(res, "*")) {
				resAllowed = true
				break
			}
		}
		if !resAllowed {
			return fmt.Errorf("policy violation: resource '%s' is not in the allowlist", cmd.Resource)
		}
	}

	if cmd.Limit > 0 && rule.MaxLimit > 0 && cmd.Limit > rule.MaxLimit {
		return fmt.Errorf("policy violation: requested limit %d exceeds max permitted limit %d", cmd.Limit, rule.MaxLimit)
	}

	return nil
}
