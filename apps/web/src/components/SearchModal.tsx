"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  X,
  Workflow,
  Database,
  PlayCircle,
  AlertTriangle,
  Zap,
  ArrowRight,
  CornerDownLeft,
  Command,
} from "lucide-react";
import { fetchFromApi } from "@/lib/api";

export interface SearchHighlight {
  field: string;
  snippet: string;
  matched_terms: string[];
}

export interface SearchResultItem {
  id: string;
  tenant_id: string;
  entity_type: "workflow" | "connection" | "run" | "incident" | "action" | string;
  title: string;
  description: string;
  status?: string;
  url?: string;
  score: number;
  highlights: SearchHighlight[];
  metadata: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  total_hits: number;
  took_ms: number;
  results: SearchResultItem[];
  facet_distribution: Record<string, number>;
}

const CATEGORIES = [
  { id: "all", label: "All" },
  { id: "workflow", label: "Workflows" },
  { id: "connection", label: "Connections" },
  { id: "run", label: "Runs" },
  { id: "incident", label: "Incidents" },
  { id: "action", label: "Quick Actions" },
];

export function SearchModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [tookMs, setTookMs] = useState(0);
  const [totalHits, setTotalHits] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      performSearch(query, selectedCategory);
    } else {
      setSelectedIndex(0);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const performSearch = useCallback(
    async (q: string, category: string) => {
      setIsLoading(true);
      const typeParam = category !== "all" ? `&types=${category}` : "";
      const endpoint = `/api/v1/search?q=${encodeURIComponent(q)}${typeParam}&limit=20`;

      const fallback: SearchResponse = {
        query: q,
        total_hits: 0,
        took_ms: 0,
        results: [],
        facet_distribution: {},
      };

      const data = await fetchFromApi<SearchResponse>(endpoint, fallback);
      setResults(data.results || []);
      setTotalHits(data.total_hits || 0);
      setTookMs(data.took_ms || 0);
      setSelectedIndex(0);
      setIsLoading(false);
    },
    []
  );

  useEffect(() => {
    if (!isOpen) return;
    const timer = setTimeout(() => {
      performSearch(query, selectedCategory);
    }, 50);
    return () => clearTimeout(timer);
  }, [query, selectedCategory, isOpen, performSearch]);

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (results.length ? (prev + 1) % results.length : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (results.length ? (prev - 1 + results.length) % results.length : 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[selectedIndex]) {
        handleSelect(results[selectedIndex]);
      }
    }
  };

  const handleSelect = (item: SearchResultItem) => {
    onClose();
    if (item.url) {
      router.push(item.url);
    }
  };

  if (!isOpen) return null;

  const getEntityIcon = (type: string) => {
    switch (type) {
      case "workflow":
        return <Workflow className="w-4 h-4 text-[#874436]" />;
      case "connection":
        return <Database className="w-4 h-4 text-[#3A6B52]" />;
      case "run":
        return <PlayCircle className="w-4 h-4 text-[#455CA1]" />;
      case "incident":
        return <AlertTriangle className="w-4 h-4 text-[#A84232]" />;
      case "action":
      default:
        return <Zap className="w-4 h-4 text-[#8A6D3B]" />;
    }
  };

  const renderHighlight = (text: string) => {
    if (!text) return null;

    const parts = text.split(/(<mark>.*?<\/mark>)/g);
    return (
      <span>
        {parts.map((part, idx) => {
          if (part.startsWith("<mark>") && part.endsWith("</mark>")) {
            const clean = part.replace(/<\/?mark>/g, "");
            return (
              <span key={idx} className="bg-[#EADDCF] text-[#874436] font-semibold px-0.5 rounded">
                {clean}
              </span>
            );
          }
          return part;
        })}
      </span>
    );
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center pt-20 px-4 animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-[#FAF8F5] border border-[#D5CABE] shadow-2xl rounded-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[80vh]"
        onClick={(e) => e.stopPropagation()}
      >

        <div className="p-4 border-b border-[#D5CABE] flex items-center gap-3 bg-[#F3EFEA]">
          <Search className="w-5 h-5 text-[#874436] flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Search workflows, connections, runs, incidents, or commands..."
            className="w-full bg-transparent text-sm text-[#1B1B1B] placeholder-[#968676] focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="p-1 rounded hover:bg-[#E4DCCE] text-[#968676]"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="px-2 py-0.5 text-[10px] font-semibold bg-[#E7E0D6] border border-[#D5CABE] text-[#6B5E51] rounded shadow-sm">
            ESC
          </kbd>
        </div>

        <div className="flex items-center gap-1.5 px-4 py-2 border-b border-[#D5CABE] bg-[#FAF8F5] overflow-x-auto">
          {CATEGORIES.map((cat) => {
            const isActive = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  isActive
                    ? "bg-[#874436] text-white shadow-sm"
                    : "bg-[#F3EFEA] text-[#6B5E51] hover:bg-[#EAE4DC]"
                }`}
              >
                {cat.label}
              </button>
            );
          })}
          {tookMs > 0 && (
            <span className="ml-auto text-[10px] text-[#968676] font-mono">
              {totalHits} hits in {tookMs}ms
            </span>
          )}
        </div>

        <div ref={listRef} className="flex-1 overflow-y-auto p-2 space-y-1">
          {isLoading ? (
            <div className="p-8 text-center text-xs text-[#968676]">
              Searching index across lexical & semantic towers...
            </div>
          ) : results.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-sm font-medium text-[#1B1B1B]">No matching results</p>
              <p className="text-xs text-[#968676] mt-1">
                Try typing a workflow name, connection type like <code className="text-[#874436]">postgres</code>, run ID <code className="text-[#874436]">RUN-92831</code>, or partial prefix.
              </p>
            </div>
          ) : (
            results.map((item, index) => {
              const isSelected = index === selectedIndex;
              const titleSnippet = item.highlights.find((h) => h.field === "title")?.snippet;
              const descSnippet = item.highlights.find((h) => h.field === "description")?.snippet;

              return (
                <div
                  key={`${item.entity_type}_${item.id}`}
                  onClick={() => handleSelect(item)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`px-3.5 py-2.5 rounded-xl cursor-pointer flex items-center justify-between gap-3 transition-all ${
                    isSelected
                      ? "bg-[#EFE8DF] border-l-4 border-[#874436] shadow-sm"
                      : "hover:bg-[#F3EFEA] border-l-4 border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="p-2 rounded-lg bg-[#FAF8F5] border border-[#D5CABE] flex-shrink-0">
                      {getEntityIcon(item.entity_type)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-[#1B1B1B] truncate">
                          {titleSnippet ? renderHighlight(titleSnippet) : item.title}
                        </span>
                        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#EAE4DC] text-[#6B5E51]">
                          {item.entity_type}
                        </span>
                        {item.status && (
                          <span
                            className={`text-[10px] font-semibold px-1.5 py-0.2 rounded-full ${
                              item.status.toLowerCase() === "healthy" ||
                              item.status.toLowerCase() === "active" ||
                              item.status.toLowerCase() === "completed" ||
                              item.status.toLowerCase() === "success"
                                ? "bg-[#EBF3ED] text-[#2E6B47]"
                                : item.status.toLowerCase() === "failed" ||
                                  item.status.toLowerCase() === "critical"
                                ? "bg-[#FBEBE8] text-[#A84232]"
                                : "bg-[#F0F3FA] text-[#455CA1]"
                            }`}
                          >
                            {item.status}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#7A6B5E] truncate mt-0.5">
                        {descSnippet ? renderHighlight(descSnippet) : item.description}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1 text-[#968676] flex-shrink-0">
                    {isSelected ? (
                      <span className="flex items-center gap-1 text-[11px] font-medium text-[#874436]">
                        Open <CornerDownLeft className="w-3 h-3" />
                      </span>
                    ) : (
                      <ArrowRight className="w-3.5 h-3.5 opacity-40" />
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="px-4 py-2 bg-[#F3EFEA] border-t border-[#D5CABE] flex items-center justify-between text-[11px] text-[#6B5E51]">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-[#E7E0D6] border border-[#D5CABE] rounded text-[10px]">↑</kbd>
              <kbd className="px-1.5 py-0.5 bg-[#E7E0D6] border border-[#D5CABE] rounded text-[10px]">↓</kbd>
              Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-[#E7E0D6] border border-[#D5CABE] rounded text-[10px]">↵</kbd>
              Select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-[#E7E0D6] border border-[#D5CABE] rounded text-[10px]">ESC</kbd>
              Dismiss
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[#874436] font-medium">
            <Command className="w-3 h-3" />
            <span>Hybrid Search Engine v1.0</span>
          </div>
        </div>
      </div>
    </div>
  );
}
