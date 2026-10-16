"use client";

import { motion } from "framer-motion";
import { Globe, Database, Cpu, Lock } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

const stagger = {
  visible: { transition: { staggerChildren: 0.08 } },
};

export function ArchitectureSection() {
  const layers = [
    { label: "Frontend", tech: "Next.js + Tailwind + Framer Motion", color: "bg-blue-500/20 text-blue-300 border-blue-500/30" },
    { label: "API Gateway", tech: "Node.js + Express", color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" },
    { label: "RAG Engine", tech: "Python FastAPI + Groq LLM", color: "bg-purple-500/20 text-purple-300 border-purple-500/30" },
    { label: "Data Layer", tech: "MongoDB + Vector Embeddings", color: "bg-amber-500/20 text-amber-300 border-amber-500/30" },
    { label: "Storage", tech: "IPFS via Pinata", color: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30" },
    { label: "Blockchain", tech: "Solidity on Base Sepolia", color: "bg-rose-500/20 text-rose-300 border-rose-500/30" },
  ];

  return (
    <section id="architecture" className="bg-mist py-24 text-slate-900">
      <div className="shell">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
          className="mb-12"
        >
          <motion.span variants={fadeUp} custom={0} className="section-label border-slate-200 bg-white text-slate-600">
            System Architecture
          </motion.span>
          <motion.h2 variants={fadeUp} custom={1} className="mt-5 text-3xl font-semibold tracking-tight sm:text-4xl max-w-lg">
            Production-grade, end-to-end compliance infrastructure.
          </motion.h2>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
        >
          {layers.map((layer, i) => (
            <motion.div
              key={layer.label}
              variants={fadeUp}
              custom={i}
              className="rounded-[1.6rem] border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md"
            >
              <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${layer.color}`}>
                {layer.label}
              </span>
              <p className="mt-4 text-lg font-semibold text-slate-900">{layer.tech}</p>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
          className="mt-12 rounded-[2rem] border border-slate-200 bg-white p-8"
        >
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500">
              {[
                { icon: Globe, label: "359 PDFs Ingested" },
                { icon: Database, label: "10,582 Chunks Embedded" },
                { icon: Cpu, label: "Hybrid RAG + Rules" },
                { icon: Lock, label: "On-Chain Proofs" },
              ].map((item) => (
                <span key={item.label} className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 px-3 py-1.5 text-xs">
                  <item.icon className="w-3.5 h-3.5" />
                  {item.label}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
