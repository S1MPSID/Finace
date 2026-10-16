"use client";

import { motion } from "framer-motion";
import { Search, ShieldCheck, Cpu, FileText, Lock, BarChart3 } from "lucide-react";

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
