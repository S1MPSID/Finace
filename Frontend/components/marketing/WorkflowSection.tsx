"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

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
