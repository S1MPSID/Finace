"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  ShieldCheck,
  Zap,
  FileText,
  Lock,
  Search,
  BarChart3,
  ArrowRight,
  ChevronRight,
  Database,
  Cpu,
  Globe,
} from "lucide-react";

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

export function Hero() {
  return (
    <section className="relative overflow-hidden pb-24 pt-10">
      <div className="shell">
        <div className="relative overflow-hidden rounded-[2.5rem] border border-white/10 bg-[#0b0f0f] px-6 py-12 shadow-glow sm:px-10 lg:px-16 lg:py-20">
          {/* Animated background */}
          <div className="absolute inset-0 grid-lines opacity-15" />
          <motion.div
            className="absolute -left-32 top-20 h-96 w-96 rounded-full bg-accent/15 blur-[100px]"
            animate={{ scale: [1, 1.2, 1], opacity: [0.15, 0.25, 0.15] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute right-0 top-0 h-80 w-80 rounded-full bg-emerald/25 blur-[100px]"
            animate={{ scale: [1, 1.15, 1], opacity: [0.2, 0.35, 0.2] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          />
          <motion.div
            className="absolute bottom-0 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-blue-500/10 blur-[80px]"
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          />

          <div className="relative flex flex-col items-center text-center">
            <motion.div initial="hidden" animate="visible" variants={stagger} className="max-w-4xl">
              <motion.span variants={fadeUp} custom={0} className="section-label">
                AI-Powered Compliance Engine
              </motion.span>
              <motion.h1 variants={fadeUp} custom={1} className="headline mt-6 !leading-[1.1]">
                Autonomous compliance intelligence for{" "}
                <span className="bg-gradient-to-r from-accent via-emerald-300 to-accent bg-clip-text text-transparent">
                  fintech startups
                </span>
              </motion.h1>
              <motion.p variants={fadeUp} custom={2} className="subcopy mt-6 mx-auto !text-base !leading-8 max-w-2xl">
                Analyze workflows against RBI, FATF, and NPCI regulations using RAG + AI reasoning.
                Get explainable risk reports, generate legal documents, and anchor compliance proofs
                on the blockchain — all from one dashboard.
              </motion.p>
              <motion.div variants={fadeUp} custom={3} className="mt-8 flex flex-wrap justify-center gap-3">
                <Link
                  href="/login"
                  className="group inline-flex items-center gap-2 rounded-full bg-accent px-6 py-3.5 text-sm font-semibold text-ink transition-all hover:bg-white hover:shadow-[0_0_30px_rgba(126,240,207,0.4)]"
                >
                  Launch Dashboard
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.05] px-6 py-3.5 text-sm font-semibold text-white transition hover:border-accent/40 hover:bg-white/[0.08]"
                >
                  How It Works
                  <ChevronRight className="w-4 h-4" />
                </a>
              </motion.div>

              <motion.div variants={fadeUp} custom={4} className="mt-14 flex flex-wrap justify-center gap-10 text-sm text-white/60">
                {[
                  { stat: "359", label: "Regulations indexed", icon: Database },
                  { stat: "10,582", label: "Compliance clauses", icon: Search },
                  { stat: "Base Sepolia", label: "Blockchain anchored", icon: Lock },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-3 text-left">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/[0.06] border border-white/8">
                      <item.icon className="w-4 h-4 text-accent" />
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-white">{item.stat}</p>
                      <p className="text-xs text-white/50">{item.label}</p>
                    </div>
                  </div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────── Navbar ─────────────── */

export function Navbar() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="shell pt-6"
    >
      <div className="glass flex items-center justify-between rounded-full px-5 py-3">
        <Link href="/" className="flex items-center gap-2 text-sm font-bold tracking-[0.24em] text-white/90 uppercase">
          <ShieldCheck className="w-5 h-5 text-accent" />
          Finace
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-white/65 md:flex">
          {[
            { label: "Features", href: "#capabilities" },
            { label: "How It Works", href: "#how-it-works" },
            { label: "Architecture", href: "#architecture" },
          ].map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="transition hover:text-white"
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-1.5 text-xs text-white/40 sm:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Systems Online
          </span>
          <Link
            href="/login"
            className="rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-ink transition hover:bg-white hover:shadow-[0_0_20px_rgba(126,240,207,0.3)]"
          >
            Sign In
          </Link>
        </div>
      </div>
    </motion.div>
  );
}

/* ─────────────── Capabilities ─────────────── */

const capabilities = [
  {
    icon: Search,
    title: "RAG-Powered Analysis",
    description: "10,582 regulatory clauses embedded and searchable. Query any compliance topic and get cited, explainable answers.",
  },
  {
    icon: ShieldCheck,
    title: "Workflow Risk Detection",
    description: "Submit product workflows and get AI + rule-based risk assessments with severity scoring and clause references.",
  },
  {
    icon: Cpu,
    title: "Hybrid Intelligence",
    description: "Deterministic rule engine merged with LLM reasoning. Not a chatbot — a compliance decision engine.",
  },
  {
    icon: FileText,
    title: "Legal Document Studio",
    description: "Generate first-draft Privacy Policies and Terms of Service directly from your compliance analysis data.",
  },
  {
    icon: Lock,
    title: "Immutable Audit Trail",
    description: "Reports are hashed, uploaded to IPFS via Pinata, and anchored to Base Sepolia for cryptographic traceability.",
  },
  {
    icon: BarChart3,
    title: "Evaluator Console",
    description: "Dedicated review surface for auditors to verify AI findings, approve reports, and leave structured remarks.",
  },
];

export function CapabilitiesSection() {
  return (
    <section id="capabilities" className="py-24">
      <div className="shell">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={stagger}
          className="mb-12 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
        >
          <motion.div variants={fadeUp} custom={0}>
            <span className="section-label">Platform Capabilities</span>
            <h2 className="mt-5 text-3xl font-semibold tracking-tight text-white sm:text-4xl max-w-lg">
              Everything your compliance team needs — in one surface.
            </h2>
          </motion.div>
          <motion.p variants={fadeUp} custom={1} className="max-w-xl text-sm leading-7 text-white/60">
            From regulatory Q&A to blockchain-anchored audit proofs. Each module works together
            as a unified compliance decision engine.
          </motion.p>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          variants={stagger}
          className="grid gap-5 md:grid-cols-2 xl:grid-cols-3"
        >
          {capabilities.map((item, i) => (
            <motion.div
              key={item.title}
              variants={fadeUp}
              custom={i}
              className="group glass rounded-[1.8rem] p-6 transition-all hover:border-accent/30 hover:bg-white/[0.06] hover:shadow-[0_0_40px_rgba(126,240,207,0.08)]"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 border border-accent/20 mb-5 transition-colors group-hover:bg-accent/20">
                <item.icon className="w-5 h-5 text-accent" />
              </div>
              <h3 className="text-xl font-semibold text-white">{item.title}</h3>
              <p className="mt-3 text-sm leading-7 text-white/60">{item.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

/* ─────────────── How It Works ─────────────── */

const workflowSteps = [
  { step: "01", title: "Ingest Regulations", desc: "Parse 359+ RBI, FATF, and NPCI documents into structured chunks with metadata." },
  { step: "02", title: "Embed & Index", desc: "Generate 1024-dim vector embeddings and store in MongoDB for semantic retrieval." },
  { step: "03", title: "Analyze with RAG", desc: "Submit workflows. AI retrieves relevant clauses and reasons over them with Groq LLM." },
  { step: "04", title: "Explain & Score", desc: "Get risk levels, clause citations, reasoning steps, and compliance scores in structured JSON." },
  { step: "05", title: "Anchor & Prove", desc: "Generate PDF reports, upload to IPFS, and write proof hashes to Base Sepolia blockchain." },
];

export function WorkflowSection() {
  return (
    <section id="how-it-works" className="py-24">
      <div className="shell grid gap-10 lg:grid-cols-[0.85fr_1.15fr]">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
          className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-[#0d1413] to-[#11231f] p-8 shadow-glow lg:sticky lg:top-8 lg:self-start"
        >
          <motion.span variants={fadeUp} custom={0} className="section-label">System Pipeline</motion.span>
          <motion.h2 variants={fadeUp} custom={1} className="mt-5 text-3xl font-semibold tracking-tight text-white">
            From regulatory PDF to blockchain proof in 5 steps.
          </motion.h2>
          <motion.p variants={fadeUp} custom={2} className="mt-5 text-sm leading-7 text-white/60">
            Users see where every answer comes from, what&apos;s risky, and what proof was recorded — no
            technical logs required.
          </motion.p>
          <motion.div variants={fadeUp} custom={3}>
            <Link
              href="/login"
              className="mt-8 inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-ink transition hover:bg-white"
            >
              Try It Now <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={stagger}
          className="grid gap-4"
        >
          {workflowSteps.map((item, i) => (
            <motion.div
              key={item.step}
              variants={fadeUp}
              custom={i}
              className="glass group flex items-start gap-5 rounded-[1.6rem] px-6 py-6 transition-all hover:border-accent/25 hover:bg-white/[0.06]"
            >
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-accent/10 border border-accent/20 text-sm font-bold text-accent transition group-hover:bg-accent group-hover:text-ink">
                {item.step}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-7 text-white/55">{item.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

/* ─────────────── Architecture ─────────────── */

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

/* ─────────────── CTA + Footer ─────────────── */

export function CTASection() {
  return (
    <section className="py-24">
      <div className="shell">
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative overflow-hidden rounded-[2.5rem] border border-accent/20 bg-gradient-to-br from-accent/20 via-[#0e1c19] to-[#091010] px-8 py-16 text-center shadow-glow sm:px-12 lg:py-20"
        >
          <motion.div
            className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/15 blur-[80px]"
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ duration: 6, repeat: Infinity }}
          />
          <motion.div
            className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-emerald/20 blur-[80px]"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 8, repeat: Infinity }}
          />

          <div className="relative">
            <ShieldCheck className="w-12 h-12 text-accent mx-auto mb-6" />
            <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl lg:text-5xl">
              Ready to automate your compliance?
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-sm leading-7 text-white/60 sm:text-base">
              Submit your first workflow, get an AI-powered risk analysis, and anchor your compliance
              proof on the blockchain — all in under 2 minutes.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/login"
                className="group inline-flex items-center gap-2 rounded-full bg-accent px-7 py-4 text-sm font-semibold text-ink transition-all hover:bg-white hover:shadow-[0_0_30px_rgba(126,240,207,0.4)]"
              >
                Launch Dashboard
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link
                href="/login"
                className="rounded-full border border-white/15 bg-white/[0.05] px-7 py-4 text-sm font-semibold text-white transition hover:border-accent/40 hover:bg-white/[0.08]"
              >
                Sign In
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-white/8 py-10">
      <div className="shell flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-white/50">
          <ShieldCheck className="w-4 h-4 text-accent" />
          <span className="font-semibold text-white/70">Finace</span>
          <span>— Autonomous Compliance Engine</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-white/40">
          <span>RAG + Rules Hybrid</span>
          <span className="h-3 w-px bg-white/15" />
          <span>Base Sepolia</span>
          <span className="h-3 w-px bg-white/15" />
          <span>IPFS Anchored</span>
        </div>
      </div>
    </footer>
  );
}
