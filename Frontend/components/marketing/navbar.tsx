"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ShieldCheck, LayoutDashboard, ArrowRight, User as UserIcon } from "lucide-react";
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
      <div className="glass flex items-center justify-between rounded-full px-4 py-2.5 sm:px-5 sm:py-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.24em] text-white/90"
        >
          <ShieldCheck className="h-5 w-5 text-accent" />
          Finace
        </Link>

        <nav className="hidden items-center gap-6 text-sm text-white/65 md:flex">
          {[
            { label: "Features", href: "#capabilities" },
            { label: "How It Works", href: "#how-it-works" },
            { label: "Architecture", href: "#architecture" },
          ].map((item) => (
            <a key={item.label} href={item.href} className="transition hover:text-white">
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <span className="hidden items-center gap-1.5 text-xs text-white/40 lg:inline-flex">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
            Systems Online
          </span>

          {!authReady ? (
            <span className="h-9 w-28 animate-pulse rounded-full bg-white/10" />
          ) : isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] py-1 pl-1 pr-3 sm:flex">
                <span className="flex h-7 w-7 items-center justify-center rounded-full border border-accent/25 bg-accent/10 text-accent">
                  <UserIcon className="h-3.5 w-3.5" />
                </span>
                <span className="max-w-[110px] truncate text-xs font-medium text-white/85">
                  {user.name}
                </span>
              </div>
              <Link
                href={dashboardHref}
                className="inline-flex items-center gap-1.5 rounded-full bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition hover:bg-white hover:shadow-[0_0_20px_rgba(74,222,128,0.3)]"
              >
                <LayoutDashboard className="h-3.5 w-3.5" />
                Dashboard
              </Link>
            </div>
          ) : (
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-ink transition hover:bg-white hover:shadow-[0_0_20px_rgba(74,222,128,0.3)]"
            >
              Sign In
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          )}
        </div>
      </div>
    </motion.div>
  );
}
