package buffer

import (
	"os"
	"path/filepath"
	"testing"
)

func TestBuffer_EnqueueAndPeek(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "flowmesh_buffer_test_*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	dbPath := filepath.Join(tempDir, "test_buffer.db")
	buf, err := New(dbPath)
	if err != nil {
		t.Fatalf("failed to create buffer: %v", err)
	}
	defer buf.Close()

	count, err := buf.Count()
	if err != nil || count != 0 {
		t.Fatalf("expected count 0, got %d, err: %v", count, err)
	}

	id1, err := buf.Enqueue("heartbeat", map[string]interface{}{"cpu": 15.5})
	if err != nil {
		t.Fatalf("failed to enqueue 1: %v", err)
	}
	id2, err := buf.Enqueue("command_result", map[string]interface{}{"cmd_id": "c-1", "status": "ok"})
	if err != nil {
		t.Fatalf("failed to enqueue 2: %v", err)
	}

	count, err = buf.Count()
	if err != nil || count != 2 {
		t.Fatalf("expected count 2, got %d, err: %v", count, err)
	}

	events, err := buf.Peek(10)
	if err != nil {
		t.Fatalf("failed to peek: %v", err)
	}
	if len(events) != 2 {
		t.Fatalf("expected 2 events, got %d", len(events))
	}
	if events[0].ID != id1 || events[0].EventType != "heartbeat" {
		t.Errorf("unexpected event 0: %+v", events[0])
	}
	if events[1].ID != id2 || events[1].EventType != "command_result" {
		t.Errorf("unexpected event 1: %+v", events[1])
	}

	if err := buf.Delete([]int64{id1}); err != nil {
		t.Fatalf("failed to delete id1: %v", err)
	}

	count, err = buf.Count()
	if err != nil || count != 1 {
		t.Fatalf("expected count 1 after delete, got %d", count)
	}

	events, err = buf.Peek(10)
	if err != nil || len(events) != 1 {
		t.Fatalf("expected 1 remaining event, got %d", len(events))
	}
	if events[0].ID != id2 {
		t.Errorf("expected remaining event to be id2 (%d), got %d", id2, events[0].ID)
	}
}

func TestBuffer_PersistenceAcrossReopen(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "flowmesh_buffer_persist_*")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	dbPath := filepath.Join(tempDir, "persist.db")
	buf1, err := New(dbPath)
	if err != nil {
		t.Fatalf("failed to create buffer: %v", err)
	}

	_, err = buf1.Enqueue("audit", map[string]interface{}{"action": "offline_query"})
	if err != nil {
		t.Fatalf("failed to enqueue: %v", err)
	}
	buf1.Close()

	buf2, err := New(dbPath)
	if err != nil {
		t.Fatalf("failed to re-open buffer: %v", err)
	}
	defer buf2.Close()

	count, err := buf2.Count()
	if err != nil || count != 1 {
		t.Fatalf("expected persisted count 1, got %d, err: %v", count, err)
	}

	events, err := buf2.Peek(5)
	if err != nil || len(events) != 1 {
		t.Fatalf("expected 1 persisted event, got %d", len(events))
	}
	if events[0].EventType != "audit" {
		t.Errorf("unexpected persisted event type: %s", events[0].EventType)
	}
}
