package buffer

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	_ "modernc.org/sqlite"
)

type BufferedEvent struct {
	ID        int64                  `json:"id"`
	EventType string                 `json:"event_type"`
	Payload   map[string]interface{} `json:"payload"`
	CreatedAt time.Time              `json:"created_at"`
}

type Buffer struct {
	db *sql.DB
	mu sync.Mutex
}

func New(dbPath string) (*Buffer, error) {

	dsn := fmt.Sprintf("file:%s?_pragma=busy_timeout(5000)&_pragma=journal_mode(WAL)", dbPath)
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open sqlite buffer: %w", err)
	}

	schema := `
	CREATE TABLE IF NOT EXISTS offline_buffer (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		event_type TEXT NOT NULL,
		payload TEXT NOT NULL,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	);
	CREATE INDEX IF NOT EXISTS idx_buffer_created ON offline_buffer(created_at);
	`
	if _, err := db.Exec(schema); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to initialize sqlite buffer schema: %w", err)
	}

	return &Buffer{db: db}, nil
}

func (b *Buffer) Enqueue(eventType string, payload map[string]interface{}) (int64, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	raw, err := json.Marshal(payload)
	if err != nil {
		return 0, fmt.Errorf("failed to serialize payload: %w", err)
	}

	res, err := b.db.Exec(
		"INSERT INTO offline_buffer (event_type, payload, created_at) VALUES (?, ?, ?)",
		eventType, string(raw), time.Now().UTC(),
	)
	if err != nil {
		return 0, fmt.Errorf("failed to insert into buffer: %w", err)
	}

	return res.LastInsertId()
}

func (b *Buffer) Peek(limit int) ([]BufferedEvent, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	rows, err := b.db.Query(
		"SELECT id, event_type, payload, created_at FROM offline_buffer ORDER BY id ASC LIMIT ?",
		limit,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to query buffer: %w", err)
	}
	defer rows.Close()

	var events []BufferedEvent
	for rows.Next() {
		var ev BufferedEvent
		var rawPayload string
		var createdAt string

		if err := rows.Scan(&ev.ID, &ev.EventType, &rawPayload, &createdAt); err != nil {
			return nil, fmt.Errorf("failed to scan buffer row: %w", err)
		}

		if err := json.Unmarshal([]byte(rawPayload), &ev.Payload); err != nil {
			ev.Payload = map[string]interface{}{"raw": rawPayload}
		}

		parsedTime, err := time.Parse("2006-01-02 15:04:05", createdAt)
		if err == nil {
			ev.CreatedAt = parsedTime
		} else {
			ev.CreatedAt = time.Now().UTC()
		}

		events = append(events, ev)
	}

	return events, nil
}

func (b *Buffer) Delete(ids []int64) error {
	if len(ids) == 0 {
		return nil
	}

	b.mu.Lock()
	defer b.mu.Unlock()

	tx, err := b.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare("DELETE FROM offline_buffer WHERE id = ?")
	if err != nil {
		return fmt.Errorf("failed to prepare delete statement: %w", err)
	}
	defer stmt.Close()

	for _, id := range ids {
		if _, err := stmt.Exec(id); err != nil {
			return fmt.Errorf("failed to delete buffer event %d: %w", id, err)
		}
	}

	return tx.Commit()
}

func (b *Buffer) Count() (int, error) {
	b.mu.Lock()
	defer b.mu.Unlock()

	var count int
	err := b.db.QueryRow("SELECT COUNT(*) FROM offline_buffer").Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("failed to count buffered events: %w", err)
	}
	return count, nil
}

func (b *Buffer) Close() error {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.db.Close()
}
