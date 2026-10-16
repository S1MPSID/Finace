"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowRight, ShieldAlert, ChevronDown, Check, 
  MessageSquare, Send, FileCheck, RefreshCw, 
  AlertCircle, ChevronRight, User as UserIcon, Bot,
  ExternalLink
} from "lucide-react";
import { workflowApi, queryCompliance } from "@/services/api";

const REGULATORS = [
  { id: "RBI", name: "Reserve Bank of India (RBI)" },
  { id: "NPCI", name: "National Payments Corporation of India (NPCI)" },
  { id: "UAE_CBUAE", name: "CBUAE (UAE Central Bank)" },
];

interface Message {
  role: "user" | "ai";
  content: string;
  sources?: any[];
  data?: any;
}

export default function WorkflowChatPage() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [expandedSource, setExpandedSource] = useState<number | null>(null);
  
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      // Build conversation history for context
      const historyText = messages.map(m => `${m.role === 'ai' ? 'AI' : 'User'}: ${m.content}`).join('\n\n');
      const fullPrompt = messages.length > 0 
        ? `Previous Conversation Context:\n${historyText}\n\nCurrent Follow-up Question:\n${userMsg}`
        : userMsg;

      const data: any = await queryCompliance({ 
        prompt: fullPrompt,
        topK: 5
      });
      
      setMessages(prev => [...prev, { 
        role: "ai", 
        content: data.answer || data.analysis?.explanation || "I've analyzed your workflow. Does this match your intended logic?",
        sources: data.sources || data.retrieval_hits || data.analysis?.applicable_clauses || [],
        data: data.analysis || {} 
      }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: "ai", content: "Sorry, I encountered an error during analysis. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFinalizeReport = async () => {
    setFinalizing(true);
    try {
      // Compile all messages into one context for the final report
      const fullContext = messages
        .map(m => `${m.role === "user" ? "User Query" : "AI Response"}: ${m.content}`)
        .join("\n\n");

      const data: any = await workflowApi.analyze(fullContext);
      if (data && data.report_id) {
        router.push(`/dashboard/evaluator/${data.report_id}`);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to generate final report.");
    } finally {
      setFinalizing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col gap-4">
      {/* Header */}
      <div className="p-5 border-b border-white/5 flex items-center justify-between bg-white/[0.02] glass rounded-[1.8rem]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center border border-accent/20">
            <MessageSquare className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Compliance Studio</h2>
            <p className="text-xs text-white/40">Refine your workflow with AI before finalizing.</p>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 glass rounded-[2rem] overflow-hidden flex flex-col">
        <div ref={scrollRef} data-hide-scrollbar className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
          <style>{`[data-hide-scrollbar]::-webkit-scrollbar { display: none; }`}</style>
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-40 max-w-sm mx-auto">
              <Bot className="w-12 h-12 mb-4" />
              <p className="text-sm">Describe your business workflow to start the compliance analysis. You can refine the details through conversation.</p>
            </div>
          )}

          {messages.map((m, i) => {
            const backendBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api/v1").replace(/\/api\/v1\/?$/, "");
            return (
            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center border ${m.role === "user" ? "bg-white/5 border-white/10" : "bg-accent/10 border-accent/20"}`}>
                {m.role === "user" ? <UserIcon className="w-4 h-4 text-white/40" /> : <ShieldAlert className="w-4 h-4 text-accent" />}
              </div>
              <div className={`max-w-[80%] space-y-3 ${m.role === "user" ? "items-end" : ""}`}>
                <div 
                  className={`rounded-2xl p-4 text-sm leading-relaxed ${m.role === "user" ? "bg-white/[0.05] text-white/90" : "bg-accent/5 text-white/80 border border-accent/10"}`}
                  dangerouslySetInnerHTML={{ 
                    __html: m.content
                      // Replace opening heading tags with styled strong tags and spacing
                      .replace(/<h[1-6]>/gi, "<br/><br/><strong class='text-accent uppercase tracking-wider block mb-2'>")
                      // Replace closing heading tags
                      .replace(/<\/h[1-6]>/gi, "</strong>")
                      // Add some spacing to normal paragraphs if AI uses <p>
                      .replace(/<p>/gi, "<div class='mb-2'>")
                      .replace(/<\/p>/gi, "</div>") 
                  }}
                />
                {/* Sources — shown as clickable PDF links */}
                {m.role === "ai" && m.sources && m.sources.length > 0 && (
                  <div className="pt-1 space-y-1.5">
                    <p className="text-[10px] font-bold text-white/40 uppercase tracking-widest">Sources</p>
                    {m.sources.map((source: any, si: number) => {
                      const relPath = source.relative_path || source.source_file || "";
                      const hasFile = relPath && (relPath.endsWith(".pdf") || relPath.includes("/") || relPath.includes("\\"));
                      const docUrl = hasFile ? `${backendBase}/docs/${encodeURI(relPath.replace(/\\/g, "/"))}` : null;
                      const fileName = relPath ? relPath.split(/[/\\]/).pop() : (source.document_id || "Regulation");
                      return docUrl ? (
                        <a key={si} href={docUrl} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-2 text-xs text-accent hover:text-white transition group">
                          <FileCheck className="w-3.5 h-3.5 shrink-0 text-accent/60 group-hover:text-white transition" />
                          <span className="truncate">{fileName}</span>
                          <ExternalLink className="w-3 h-3 shrink-0 opacity-40 group-hover:opacity-100 transition" />
                        </a>
                      ) : (
                        <p key={si} className="text-xs text-white/40 flex items-center gap-2">
                          <FileCheck className="w-3.5 h-3.5 shrink-0" />
                          <span className="truncate">{fileName}</span>
                        </p>
                      );
                    })}
                  </div>
                )}

                {m.data?.risk_flags?.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {m.data.riskFlags.map((flag: string, fi: number) => (
                      <span key={fi} className="bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider">
                        {flag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
            );
          })}
          {loading && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center animate-pulse">
                <ShieldAlert className="w-4 h-4 text-accent" />
              </div>
              <div className="bg-white/[0.03] rounded-2xl p-4 flex gap-1 items-center h-10">
                <span className="w-1.5 h-1.5 bg-accent/40 rounded-full animate-bounce" />
                <span className="w-1.5 h-1.5 bg-accent/40 rounded-full animate-bounce [animation-delay:0.2s]" />
                <span className="w-1.5 h-1.5 bg-accent/40 rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          )}
        </div>
      }
    >
      <WorkflowChatPage />
    </Suspense>
  );
}
