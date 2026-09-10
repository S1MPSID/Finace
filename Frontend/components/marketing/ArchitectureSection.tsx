"use client";

import { motion } from "framer-motion";
import {
  Globe,
  Database,
  Cpu,
  Lock,
  Layout,
  Server,
  BrainCircuit,
  HardDrive,
  Link2,
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.07, duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

const stagger = {
  visible: { transition: { staggerChildren: 0.07 } },
};

const layers = [
  { label: "Frontend", tech: "Next.js + Tailwind + Framer Motion", icon: Layout },
  { label: "API Gateway", tech: "Node.js + Express", icon: Server },
  { label: "RAG Engine", tech: "Python FastAPI + Gemini LLM", icon: BrainCircuit },
  { label: "Data Layer", tech: "MongoDB Atlas + Vector Embeddings", icon: Database },
  { label: "Storage", tech: "IPFS via Pinata", icon: HardDrive },
  { label: "Blockchain", tech: "Solidity on Base Sepolia", icon: Link2 },
];

const pipeline = [
  { icon: Globe, label: "359 PDFs", sub: "Ingested" },
  { icon: Database, label: "10,582 Chunks", sub: "Embedded" },
  { icon: Cpu, label: "Hybrid RAG", sub: "Rules + LLM" },
  { icon: Lock, label: "On-Chain", sub: "Proofs" },
];

export function ArchitectureSection() {
  return (
    <section id="architecture" className="relative py-24">
      <div className="shell">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
          className="mb-12 max-w-xl"
        >
          <motion.span variants={fadeUp} custom={0} className="section-label">
            System Architecture
          </motion.span>
          <motion.h2
            variants={fadeUp}
            custom={1}
            className="mt-5 text-3xl font-semibold tracking-tight text-white sm:text-4xl"
          >
            Production-grade, end-to-end compliance infrastructure.
          </motion.h2>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
          className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
        >
          {layers.map((layer, i) => {
            const Icon = layer.icon;
            return (
              <motion.div
                key={layer.label}
                variants={fadeUp}
                custom={i}
                className="group rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-sm transition hover:border-accent/30 hover:bg-accent/[0.06]"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-accent/25 bg-accent/10 text-accent transition group-hover:border-accent/40 group-hover:bg-accent/15">
                    <Icon className="h-4 w-4" strokeWidth={1.85} />
                  </div>
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-0.5 text-[11px] font-medium text-accent/90">
                    {layer.label}
                  </span>
                </div>
                <p className="mt-4 text-[15px] font-semibold leading-snug text-white/90">{layer.tech}</p>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Compact horizontal proof strip */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="relative mt-10 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-5 backdrop-blur-sm sm:px-6"
        >
          <div className="absolute left-[8%] right-[8%] top-1/2 hidden h-px -translate-y-1/2 bg-gradient-to-r from-transparent via-accent/35 to-transparent sm:block" />

          <div className="relative grid grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-2">
            {pipeline.map((item, i) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="relative flex flex-col items-center text-center">
                  <div className="z-10 mb-2 flex h-9 w-9 items-center justify-center rounded-full border border-accent/35 bg-[#0a1210] text-accent shadow-[0_0_16px_rgba(74,222,128,0.12)]">
                    <Icon className="h-3.5 w-3.5" strokeWidth={2} />
                  </div>
                  <p className="text-[13px] font-semibold text-white">{item.label}</p>
                  <p className="mt-0.5 text-[11px] text-white/45">{item.sub}</p>
                  {i < pipeline.length - 1 && (
                    <span className="absolute right-[-6%] top-[18px] hidden text-accent/30 sm:block">›</span>
                  )}
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
