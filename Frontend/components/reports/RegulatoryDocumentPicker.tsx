"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, FileText, Loader2, Search } from "lucide-react";
import type { DocEntry } from "@/lib/docs/docCatalog";

type Props = {
  catalog: DocEntry[];
  value: string;
  onChange: (path: string) => void;
  disabled?: boolean;
  loading?: boolean;
};

function labelFor(path: string, catalog: DocEntry[]): string {
  const hit = catalog.find((d) => d.path === path);
  if (!hit) return "";
  return `[${hit.category}] ${hit.label}`;
}

export function RegulatoryDocumentPicker({ catalog, value, onChange, disabled, loading }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const grouped = useMemo(() => {
    const q = query.trim().toLowerCase();
    const map = new Map<string, DocEntry[]>();
    for (const doc of catalog) {
      if (q && !doc.label.toLowerCase().includes(q) && !doc.category.toLowerCase().includes(q)) {
        continue;
      }
      const list = map.get(doc.category) || [];
      list.push(doc);
      map.set(doc.category, list);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [catalog, query]);

  const selectedLabel = value ? labelFor(value, catalog) : "";

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        disabled={disabled || loading}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 rounded-xl border border-white/10 bg-[#0d1413] px-3 py-2.5 text-left text-sm text-white transition hover:border-white/20 disabled:opacity-50"
      >
        <span className="flex min-w-0 items-center gap-2">
          {loading ? (
            <Loader2 className="h-4 w-4 shrink-0 animate-spin text-accent" />
          ) : (
            <FileText className="h-4 w-4 shrink-0 text-accent/70" />
          )}
          <span className={`truncate ${selectedLabel ? "text-white" : "text-white/45"}`}>
            {loading ? "Loading documents…" : selectedLabel || "Select a document from the library…"}
          </span>
        </span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-white/40 transition ${open ? "rotate-180" : ""}`} />
      </button>

      {open && !disabled && !loading && (
        <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-xl border border-white/10 bg-[#0d1413] shadow-2xl shadow-black/50">
          <div className="border-b border-white/8 p-2">
            <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1.5">
              <Search className="h-3.5 w-3.5 text-white/35" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search documents…"
                className="w-full bg-transparent text-xs text-white outline-none placeholder:text-white/35"
                autoFocus
              />
            </div>
          </div>

          <div className="max-h-56 overflow-y-auto p-1.5 [scrollbar-width:thin]">
            {grouped.length === 0 ? (
              <p className="px-3 py-4 text-center text-xs text-white/40">No documents match your search.</p>
            ) : (
              grouped.map(([category, docs]) => (
                <div key={category} className="mb-1">
                  <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-accent/70">
                    {category}
                  </p>
                  {docs.map((doc) => {
                    const active = doc.path === value;
                    return (
                      <button
                        key={doc.path}
                        type="button"
                        onClick={() => {
                          onChange(doc.path);
                          setOpen(false);
                          setQuery("");
                        }}
                        className={`flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left text-xs transition ${
                          active
                            ? "bg-accent/15 text-accent"
                            : "text-white/75 hover:bg-white/[0.06] hover:text-white"
                        }`}
                      >
                        <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 opacity-70" />
                        <span className="leading-snug">{doc.label}</span>
                      </button>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
