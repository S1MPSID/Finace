"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, ChevronRight, Database, Search, Lock } from "lucide-react";
import { useAppSelector } from "@/store/hooks";

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
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  const user = useAppSelector((s) => s.auth.user);

  const primaryHref = isAuthenticated
    ? user?.role === "evaluator"
      ? "/dashboard/evaluator"
      : "/dashboard/workflow"
    : "/login";

  const primaryLabel = isAuthenticated ? "Open Compliance Studio" : "Launch Dashboard";

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
