"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, ShieldCheck } from "lucide-react";

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
