"use client";

import React, { useState, useMemo } from "react";

export interface ColumnDef<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

interface MaterialDataGridProps<T> {
  title: string;
  columns: ColumnDef<T>[];
  data: T[];
  searchPlaceholder?: string;
  pageSize?: number;
  onRowClick?: (item: T) => void;
}

export function MaterialDataGrid<T extends { id: string | number }>({
  title,
  columns,
  data,
  searchPlaceholder = "Filter records...",
  pageSize = 10,
  onRowClick,
}: MaterialDataGridProps<T>) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState<boolean>(true);
  const [page, setPage] = useState(0);

  const filteredData = useMemo(() => {
    return data.filter((item) => {
      if (!searchTerm) return true;
      return Object.values(item).some((val) =>
        String(val).toLowerCase().includes(searchTerm.toLowerCase())
      );
    });
  }, [data, searchTerm]);

  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const aVal = (a as any)[sortKey];
      const bVal = (b as any)[sortKey];
      if (aVal < bVal) return sortAsc ? -1 : 1;
      if (aVal > bVal) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortKey, sortAsc]);

  const totalPages = Math.ceil(sortedData.length / pageSize);
  const pagedData = sortedData.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  return (
    <div
      className="enterprise-material-card"
      style={{
        borderRadius: "12px",
        background: "var(--card-bg, #0f172a)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        boxShadow: "0 4px 20px -2px rgba(0, 0, 0, 0.5)",
        overflow: "hidden",
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      }}
    >
      {}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "18px 24px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        <div>
          <h2
            style={{
              fontSize: "1.1rem",
              fontWeight: 600,
              color: "#f8fafc",
              margin: 0,
              letterSpacing: "-0.01em",
            }}
          >
            {title}
          </h2>
          <span
            style={{
              fontSize: "0.78rem",
              color: "#94a3b8",
            }}
          >
            Showing {filteredData.length} records
          </span>
        </div>

        {}
        <div>
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(0);
            }}
            style={{
              padding: "8px 14px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#f1f5f9",
              fontSize: "0.85rem",
              outline: "none",
              transition: "border-color 0.2s, box-shadow 0.2s",
            }}
          />
        </div>
      </div>

      {}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            textAlign: "left",
          }}
        >
          <caption className="sr-only">{title} Data Grid</caption>
          <thead>
            <tr
              style={{
                background: "rgba(255, 255, 255, 0.02)",
                borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
              }}
            >
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  onClick={() => col.sortable && handleSort(String(col.key))}
                  style={{
                    padding: "12px 20px",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    color: "#94a3b8",
                    cursor: col.sortable ? "pointer" : "default",
                    userSelect: "none",
                    width: col.width,
                  }}
                >
                  {col.header}
                  {col.sortable && sortKey === col.key && (
                    <span style={{ marginLeft: "6px", color: "#38bdf8" }}>
                      {sortAsc ? "▲" : "▼"}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pagedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  style={{
                    padding: "36px 20px",
                    textAlign: "center",
                    color: "#64748b",
                    fontSize: "0.9rem",
                  }}
                >
                  No matching enterprise records found.
                </td>
              </tr>
            ) : (
              pagedData.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => onRowClick && onRowClick(row)}
                  style={{
                    borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                    cursor: onRowClick ? "pointer" : "default",
                    transition: "background-color 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor =
                      "rgba(255, 255, 255, 0.03)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "transparent";
                  }}
                >
                  {columns.map((col) => (
                    <td
                      key={String(col.key)}
                      style={{
                        padding: "14px 20px",
                        fontSize: "0.85rem",
                        color: "#e2e8f0",
                        verticalAlign: "middle",
                      }}
                    >
                      {col.render
                        ? col.render(row)
                        : String((row as any)[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "14px 24px",
          borderTop: "1px solid rgba(255, 255, 255, 0.06)",
          fontSize: "0.8rem",
          color: "#94a3b8",
        }}
      >
        <span>
          Page {page + 1} of {Math.max(totalPages, 1)}
        </span>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            style={{
              padding: "6px 14px",
              borderRadius: "6px",
              background:
                page === 0 ? "rgba(255,255,255,0.02)" : "rgba(255,255,255,0.08)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: page === 0 ? "#475569" : "#f1f5f9",
              cursor: page === 0 ? "not-allowed" : "pointer",
              fontSize: "0.8rem",
              fontWeight: 500,
            }}
          >
            Previous
          </button>
          <button
            type="button"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            style={{
              padding: "6px 14px",
              borderRadius: "6px",
              background:
                page >= totalPages - 1
                  ? "rgba(255,255,255,0.02)"
                  : "rgba(255,255,255,0.08)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: page >= totalPages - 1 ? "#475569" : "#f1f5f9",
              cursor: page >= totalPages - 1 ? "not-allowed" : "pointer",
              fontSize: "0.8rem",
              fontWeight: 500,
            }}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
