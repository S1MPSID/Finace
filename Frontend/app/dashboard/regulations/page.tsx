"use client";

import { useState, useEffect, useMemo } from "react";
import { docsApi } from "@/services/api";
import { Search, BookOpen, Database, Loader2, Folder, FileText, ExternalLink, ChevronDown, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface DocFile {
  name: string;
  path: string;
}

interface DocCategory {
  category: string;
  files: DocFile[];
}

export default function RegulationsPage() {
  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState<DocCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Keep track of which categories are expanded
  const [expandedCats, setExpandedCats] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchTree = async () => {
      try {
        const response: any = await docsApi.getTree();
        const data = response.data || [];
        setCategories(data);
        
        // Expand all by default initially
        const initialExpanded: Record<string, boolean> = {};
        data.forEach((cat: DocCategory) => {
          initialExpanded[cat.category] = true;
        });
        setExpandedCats(initialExpanded);
        
      } catch (err: any) {
        console.error("Failed to fetch docs tree:", err);
        setError("Unable to load regulatory documents.");
      } finally {
        setLoading(false);
      }
    };

    fetchTree();
  }, []);

  const toggleCategory = (category: string) => {
    setExpandedCats(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  // Filter logic: if search query exists, filter files within categories
  const filteredCategories = useMemo(() => {
    if (!query.trim()) return categories;
    const q = query.toLowerCase();

    return categories.map(cat => {
      const matchingFiles = cat.files.filter(f => f.name.toLowerCase().includes(q));
      return {
        ...cat,
        files: matchingFiles
      };
    }).filter(cat => cat.files.length > 0 || cat.category.toLowerCase().includes(q));
  }, [categories, query]);

  const backendBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api/v1").replace(/\/api\/v1\/?$/, "");

  const formatCategoryName = (name: string) => {
    // Check if the folder name starts with a month abbreviation (Jan, Feb, Mar, etc. or Sept)
    const dateRegex = /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/i;
    if (dateRegex.test(name)) {
      return `RBI Guidelines dated ${name}`;
    }
    // Clean up 'RBI (1)' to just 'RBI Guidelines' or leave as is if preferred
    if (name === 'RBI (1)') return 'RBI Guidelines (Part 2)';
    if (name === 'RBI') return 'RBI Guidelines';
    return name;
  };

  return (
    <div className="space-y-6">
      <div className="glass rounded-[1.8rem] p-6">
        <p className="text-sm text-accent flex items-center gap-2"><BookOpen className="w-4 h-4"/> Regulation Explorer</p>
        <h2 className="mt-3 text-3xl font-semibold text-white">Document Library</h2>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/65">
          Browse and search through all regulatory source documents, including RBI and NPCI circulars. Click on any file to open the original PDF.
        </p>

        <div className="mt-8 relative max-w-xl">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-white/30" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-white/[0.03] border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
            placeholder="Search documents by name..."
          />
        </div>
      </div>

      <div className="grid gap-4">
        {loading ? (
          <div className="glass rounded-[1.7rem] p-10 flex flex-col items-center justify-center text-white/50">
            <Loader2 className="w-8 h-8 animate-spin mb-4 text-accent" />
            <p>Loading document library...</p>
          </div>
        ) : error || filteredCategories.length === 0 ? (
          <div className="glass rounded-[1.7rem] p-12 text-center flex flex-col items-center border border-white/5 bg-black/20">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-6">
              <Database className="w-8 h-8 text-white/20" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Documents Found</h3>
            <p className="text-white/50 max-w-md">
              {error || "No documents match your search query."}
            </p>
          </div>
        ) : (
          filteredCategories.map((cat) => (
            <motion.article 
              layout
              key={cat.category} 
              className="glass rounded-[1.7rem] overflow-hidden"
            >
              <div 
                className="p-5 cursor-pointer hover:bg-white/[0.02] transition flex items-center justify-between"
                onClick={() => toggleCategory(cat.category)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center border border-accent/20">
                    <Folder className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">{formatCategoryName(cat.category)}</h3>
                    <p className="text-xs text-white/40">{cat.files.length} document{cat.files.length !== 1 ? 's' : ''}</p>
                  </div>
                </div>
                <div className="text-white/40">
                  {expandedCats[cat.category] ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                </div>
              </div>

              <AnimatePresence>
                {(expandedCats[cat.category] || (query.trim() && filteredCategories.length > 0)) && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="px-6 pb-6"
                  >
                    <div className="border-t border-white/10 pt-4 mt-2 space-y-2">
                      {cat.files.map((file, idx) => {
                        const docUrl = `${backendBase}/docs/${encodeURI(file.path.replace(/\\/g, "/"))}`;
                        return (
                          <a 
                            key={idx}
                            href={docUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="group flex items-center justify-between p-3 rounded-xl hover:bg-white/[0.04] border border-transparent hover:border-white/5 transition-all"
                          >
                            <div className="flex items-center gap-3 overflow-hidden">
                              <FileText className="w-4 h-4 text-white/40 group-hover:text-accent shrink-0 transition-colors" />
                              <span className="text-sm text-white/70 group-hover:text-white truncate transition-colors">
                                {file.name}
                              </span>
                            </div>
                            <ExternalLink className="w-4 h-4 text-white/20 group-hover:text-white/60 shrink-0 transition-colors opacity-0 group-hover:opacity-100" />
                          </a>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.article>
          ))
        )}
      </div>
    </div>
  );
}
