"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";
import { useAppSelector } from "@/store/hooks";

export function Navbar() {
  const authReady = useAppSelector((s) => s.auth.authReady);
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  const user = useAppSelector((s) => s.auth.user);

  const dashboardHref =
    user?.role === "evaluator" ? "/dashboard/evaluator" : "/dashboard/workflow";

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
