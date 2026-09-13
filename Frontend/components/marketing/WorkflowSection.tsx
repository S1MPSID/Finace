"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight,
  FileStack,
  Binary,
  BrainCircuit,
  Sparkles,
  Link2,
} from "lucide-react";

const workflowSteps = [
  {
    step: "01",
    title: "Ingest Regulations",
    desc: "Parse RBI, FATF & NPCI docs into structured chunks.",
    icon: FileStack,
  },
  {
    step: "02",
    title: "Embed & Index",
    desc: "1024-dim vectors stored in MongoDB Atlas.",
    icon: Binary,
  },
  {
    step: "03",
    title: "Analyze with RAG",
    desc: "Retrieve clauses and reason with Gemini.",
    icon: BrainCircuit,
  },
  {
    step: "04",
    title: "Explain with XAI",
    desc: "SHAP & LIME show what drove the score.",
    icon: Sparkles,
  },
  {
    step: "05",
    title: "Anchor & Prove",
    desc: "IPFS report + Base Sepolia proof hash.",
    icon: Link2,
  },
];

function StepCard({
  item,
  isActive,
  onSelect,
}: {
  item: (typeof workflowSteps)[number];
  isActive: boolean;
  onSelect: () => void;
}) {
  const Icon = item.icon;
  return (
    <button
      type="button"
      onClick={onSelect}
      onMouseEnter={onSelect}
      className={`w-full rounded-2xl border px-3 py-2.5 text-left transition lg:px-3.5 lg:py-3 ${
        isActive
          ? "border-accent/45 bg-accent/10 shadow-[0_0_24px_rgba(74,222,128,0.12)]"
          : "border-white/10 bg-[#0c1412]/85 backdrop-blur-sm hover:border-accent/25"
      }`}
    >
      <div className="flex items-start gap-2.5">
        <div
          className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
            isActive ? "border-accent bg-accent text-ink" : "border-accent/30 bg-accent/10 text-accent"
          }`}
        >
          <Icon className="h-3.5 w-3.5" strokeWidth={2} />
        </div>
        <div className="min-w-0">
          <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-accent/65">
            {item.step}
          </p>
          <h3 className="mt-0.5 text-[13px] font-semibold leading-tight text-white">{item.title}</h3>
          <p className="mt-1 text-[11px] leading-4 text-white/50">{item.desc}</p>
        </div>
      </div>
    </button>
  );
}

export function WorkflowSection() {
  const [active, setActive] = useState(2);

  return (
    <section id="how-it-works" className="relative py-20">
      <div className="shell">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <span className="section-label">System Pipeline</span>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            From regulatory PDF to blockchain proof.
          </h2>
          <p className="mt-4 text-sm leading-7 text-white/55">
            Left to right — one step above the line, the next below.
          </p>
        </div>

        {/* Desktop zigzag */}
        <div className="relative mx-auto hidden max-w-5xl md:block">
          <motion.div
            className="absolute left-[4%] right-[4%] top-1/2 h-px -translate-y-1/2 origin-left bg-gradient-to-r from-accent/10 via-accent/60 to-accent/10"
            initial={{ scaleX: 0 }}
            whileInView={{ scaleX: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
          />

          <div className="relative grid grid-cols-5 gap-2.5 lg:gap-3">
            {workflowSteps.map((item, i) => {
              const Icon = item.icon;
              const above = i % 2 === 0;
              const isActive = active === i;

              return (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, y: above ? -16 : 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.08 * i, duration: 0.45 }}
                  className="relative grid grid-rows-[1fr_auto_1fr]"
                  style={{ minHeight: 220 }}
                >
                  <div className="flex flex-col justify-end pb-2">
                    {above ? (
                      <>
                        <StepCard item={item} isActive={isActive} onSelect={() => setActive(i)} />
                        <div className="mx-auto mt-2 h-5 w-px bg-gradient-to-b from-accent/20 to-accent/70" />
                      </>
                    ) : null}
                  </div>

                  <div className="relative z-20 flex justify-center">
                    <motion.button
                      type="button"
                      onClick={() => setActive(i)}
                      onMouseEnter={() => setActive(i)}
                      animate={
                        isActive
                          ? { scale: 1.08, boxShadow: "0 0 20px rgba(74,222,128,0.45)" }
                          : { scale: 1, boxShadow: "0 0 0 rgba(74,222,128,0)" }
                      }
                      transition={{ type: "spring", stiffness: 400, damping: 24 }}
                      className={`flex h-9 w-9 items-center justify-center rounded-full border ${
                        isActive
                          ? "border-white/25 bg-accent text-ink"
                          : "border-accent/50 bg-[#0a1210] text-accent"
                      }`}
                      aria-label={item.title}
                    >
                      <Icon className="h-3.5 w-3.5" strokeWidth={2.25} />
                    </motion.button>
                  </div>

                  <div className="flex flex-col justify-start pt-2">
                    {!above ? (
                      <>
                        <div className="mx-auto mb-2 h-5 w-px bg-gradient-to-t from-accent/20 to-accent/70" />
                        <StepCard item={item} isActive={isActive} onSelect={() => setActive(i)} />
                      </>
                    ) : null}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Mobile */}
        <ol className="relative mx-auto max-w-md space-y-0 md:hidden">
          <div className="absolute bottom-3 left-[17px] top-3 w-px bg-gradient-to-b from-accent/45 via-accent/20 to-transparent" />
          {workflowSteps.map((item, i) => {
            const Icon = item.icon;
            const isActive = active === i;
            return (
              <li key={item.step} className="relative flex gap-3 pb-4 last:pb-0">
                <button
                  type="button"
                  onClick={() => setActive(i)}
                  className={`relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border ${
                    isActive ? "border-accent bg-accent text-ink" : "border-accent/40 bg-[#0c1412] text-accent"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                </button>
                <div className="min-w-0 flex-1">
                  <StepCard item={item} isActive={isActive} onSelect={() => setActive(i)} />
                </div>
              </li>
            );
          })}
        </ol>

        <div className="mt-10 flex justify-center">
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-ink transition hover:bg-white"
          >
            Try It Now <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
