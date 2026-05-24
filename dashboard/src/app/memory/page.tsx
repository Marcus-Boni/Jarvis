"use client";

import { useState } from "react";
import { Search, Trash2 } from "lucide-react";

import { AppNav } from "@/components/app-nav";
import { apiFetch } from "@/lib/api";

type MemoryItem = {
  content: string;
  metadata: Record<string, string>;
  score: number;
  source: string;
};

type MemoryResponse = {
  items?: MemoryItem[];
};

export default function MemoryPage() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    try {
      const response = await apiFetch("/api/memory/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: 10 }),
      });
      const data = (await response.json()) as MemoryResponse;
      setItems(Array.isArray(data.items) ? data.items : []);
      setError(null);
    } catch (searchError) {
      setItems([]);
      setError(searchError instanceof Error ? searchError.message : "Failed to search memory.");
    } finally {
      setIsLoading(false);
    }
  };

  const clearMemory = async () => {
    if (!window.confirm("Clear all Jarvis memory? This cannot be undone.")) return;
    try {
      await apiFetch("/api/memory/clear", { method: "POST" });
      setItems([]);
      setError(null);
    } catch (clearError) {
      setError(clearError instanceof Error ? clearError.message : "Failed to clear memory.");
    }
  };

  return (
    <main className="app-shell">
      <aside className="left-rail panel">
        <div className="rail-header">
          <span className="eyebrow">Persistent Storage</span>
          <h1>Memory Browser</h1>
          <p>Inspect semantic memory results and clear the local store explicitly.</p>
        </div>
        <AppNav />
      </aside>

      <section className="workspace">
        <header className="hero panel">
          <div>
            <span className="eyebrow">ChromaDB</span>
            <h2>Search persistent memory and clear the store when needed</h2>
          </div>
        </header>

        <section className="panel">
          <div className="composer-actions memory-actions">
            <input
              className="memory-input"
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void search();
              }}
              placeholder="Search memories..."
              value={query}
            />
            <button className="primary-button" type="button" onClick={() => void search()}>
              <Search size={16} />
              Search
            </button>
            <button className="ghost-button" type="button" onClick={() => void clearMemory()}>
              <Trash2 size={16} />
              Clear All
            </button>
          </div>

          <div className="stack-list">
            {isLoading ? <p>Searching...</p> : null}
            {error ? <p>{error}</p> : null}
            {items.map((item, index) => (
              <article key={`${item.source}-${index}`} className="list-card">
                <div className="list-row">
                  <span className="eyebrow">{item.source}</span>
                  <span className="status-chip idle">score: {item.score.toFixed(2)}</span>
                </div>
                <p>{item.content}</p>
                {Object.keys(item.metadata).length > 0 ? (
                  <p className="memory-metadata">{JSON.stringify(item.metadata)}</p>
                ) : null}
              </article>
            ))}
            {!isLoading && items.length === 0 && query ? <p>No memories found for "{query}".</p> : null}
          </div>
        </section>
      </section>

      <aside className="right-rail">
        <section className="panel">
          <span className="eyebrow">Controls</span>
          <div className="config-grid">
            <div className="config-item">
              <span>Search mode</span>
              <strong>Semantic</strong>
            </div>
            <div className="config-item">
              <span>Clear mode</span>
              <strong>Explicit only</strong>
            </div>
            <div className="config-item">
              <span>Fallback</span>
              <strong>In-memory safe</strong>
            </div>
            <div className="config-item">
              <span>Phase</span>
              <strong>3</strong>
            </div>
          </div>
        </section>
      </aside>
    </main>
  );
}
