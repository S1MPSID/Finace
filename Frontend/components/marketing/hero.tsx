"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useAppSelector } from "@/store/hooks";
import { ArrowRight, ChevronRight, Sparkles, ShieldCheck } from "lucide-react";
import {
  IconRegulationsIndexed,
  IconClausesEmbedded,
  IconProofsAnchored,
} from "@/components/marketing/HeroStatIcons";

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.09, duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

const stagger = {
  visible: { transition: { staggerChildren: 0.08 } },
};

export function Hero() {
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  const user = useAppSelector((s) => s.auth.user);

  const primaryHref = isAuthenticated
    ? user?.role === "evaluator"
      ? "/dashboard/evaluator"
      : "/dashboard/workflow"
    : "/login";

  const primaryLabel = isAuthenticated ? "Open Compliance Studio" : "Launch Dashboard";

  return (
    <section className="relative overflow-hidden pb-16 pt-8 sm:pb-20 sm:pt-10">
      <div className="shell">
        <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#0b1210]/55 px-5 py-14 shadow-glow backdrop-blur-2xl sm:rounded-[2.5rem] sm:px-10 sm:py-16 lg:px-16 lg:py-20">
          <div className="absolute inset-0 grid-lines opacity-[0.08]" />
          <motion.div
            className="absolute -left-28 top-10 h-[28rem] w-[28rem] rounded-full bg-accent/25 blur-[110px]"
            animate={{ scale: [1, 1.18, 1], opacity: [0.22, 0.4, 0.22], x: [0, 30, 0] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute -right-20 top-0 h-80 w-80 rounded-full bg-emerald-400/20 blur-[100px]"
            animate={{ scale: [1, 1.2, 1], opacity: [0.2, 0.38, 0.2] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 1.5 }}
          />
          <motion.div
            className="absolute bottom-0 left-1/2 h-56 w-56 -translate-x-1/2 rounded-full bg-teal-300/10 blur-[80px]"
            animate={{ scale: [1, 1.25, 1] }}
            transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
          />

          <div className="relative mx-auto flex max-w-4xl flex-col items-center text-center">
            <motion.div initial="hidden" animate="visible" variants={stagger}>
              <motion.div
                variants={fadeUp}
                custom={0}
                className="mb-6 flex items-center justify-center gap-2"
              >
                <span className="section-label">
                  <Sparkles className="mr-1.5 inline h-3 w-3 text-accent" />
                  AI-Powered Compliance Engine
                </span>
              </motion.div>

              <motion.p
                variants={fadeUp}
                custom={1}
                className="text-xs font-bold uppercase tracking-[0.35em] text-accent/80"
              >
                Finace
              </motion.p>

              <motion.h1
                variants={fadeUp}
                custom={2}
                className="mt-4 text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl lg:leading-[1.08]"
              >
                Compliance that{" "}
                <span className="bg-gradient-to-r from-accent via-emerald-200 to-accent bg-clip-text text-transparent">
                  explains itself
                </span>
              </motion.h1>

              <motion.p
                variants={fadeUp}
                custom={3}
                className="mx-auto mt-6 max-w-2xl text-sm leading-7 text-white/60 sm:text-base sm:leading-8"
              >
                Map product workflows to RBI, FATF, and NPCI rules with RAG + Gemini. Review SHAP/LIME
                drivers, then anchor audit-ready proofs on Base Sepolia — one studio, full traceability.
              </motion.p>

              <motion.div
                variants={fadeUp}
                custom={4}
                className="mt-9 flex flex-wrap items-center justify-center gap-3"
              >
                <Link
                  href={primaryHref}
                  className="group inline-flex items-center gap-2 rounded-full bg-accent px-6 py-3.5 text-sm font-semibold text-ink transition hover:bg-white hover:shadow-[0_0_32px_rgba(74,222,128,0.4)]"
                >
                  {primaryLabel}
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.04] px-6 py-3.5 text-sm font-semibold text-white/90 transition hover:border-accent/35 hover:bg-white/[0.07]"
                >
                  See the pipeline
                  <ChevronRight className="h-4 w-4" />
                </a>
              </motion.div>

              {isAuthenticated && (
                <motion.p
                  variants={fadeUp}
                  custom={5}
                  className="mt-4 text-xs text-white/40"
                >
                  Signed in as <span className="text-accent/80">{user?.name}</span>
                </motion.p>
              )}

              <motion.div
                variants={fadeUp}
                custom={6}
                className="mt-14 grid w-full gap-3 sm:grid-cols-3"
              >
                {[
                  { stat: "359", label: "Regulations indexed", Icon: IconRegulationsIndexed },
                  { stat: "10,582", label: "Clauses embedded", Icon: IconClausesEmbedded },
                  { stat: "Base Sepolia", label: "Proofs anchored", Icon: IconProofsAnchored },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="group flex items-center gap-3.5 rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3.5 text-left backdrop-blur-sm transition hover:border-accent/25 hover:bg-accent/[0.05]"
                  >
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-accent/25 bg-gradient-to-br from-accent/15 to-transparent shadow-[0_0_20px_rgba(74,222,128,0.08)] transition group-hover:border-accent/40">
                      <item.Icon className="h-7 w-7" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-base font-semibold text-white">{item.stat}</p>
                      <p className="truncate text-[11px] text-white/45">{item.label}</p>
                    </div>
                  </div>
                ))}
              </motion.div>

              <motion.div
                variants={fadeUp}
                custom={7}
                className="mt-8 inline-flex items-center gap-2 rounded-full border border-white/8 bg-black/20 px-3 py-1.5 text-[11px] text-white/40"
              >
                <ShieldCheck className="h-3.5 w-3.5 text-accent" />
                RAG · Rules · XAI · IPFS · Blockchain
              </motion.div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
