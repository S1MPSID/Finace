"use client";

import { motion } from "framer-motion";

/** Soft animated aurora + grid — landing page only. */
export function LandingBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {/* Soft drifting grid */}
      <motion.div
        className="absolute inset-[-20%] opacity-[0.12]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(74,222,128,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(74,222,128,0.35) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse at center, black 20%, transparent 75%)",
        }}
        animate={{ x: [0, 24, 0], y: [0, 12, 0] }}
        transition={{ duration: 28, repeat: Infinity, ease: "linear" }}
      />

      {/* Aurora orbs */}
      <motion.div
        className="absolute -left-24 top-[-10%] h-[42rem] w-[42rem] rounded-full bg-accent/20 blur-[120px]"
        animate={{
          x: [0, 80, -40, 0],
          y: [0, 60, 20, 0],
          scale: [1, 1.15, 0.95, 1],
          opacity: [0.35, 0.55, 0.3, 0.35],
        }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -right-32 top-[15%] h-[36rem] w-[36rem] rounded-full bg-emerald-500/20 blur-[110px]"
        animate={{
          x: [0, -60, 30, 0],
          y: [0, 40, -30, 0],
          scale: [1, 1.2, 1.05, 1],
          opacity: [0.25, 0.45, 0.28, 0.25],
        }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut", delay: 1.5 }}
      />
      <motion.div
        className="absolute left-1/3 bottom-[-10%] h-[28rem] w-[28rem] rounded-full bg-teal-400/15 blur-[100px]"
        animate={{
          x: [0, 50, -20, 0],
          y: [0, -40, 10, 0],
          opacity: [0.2, 0.4, 0.22, 0.2],
        }}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
      />

      {/* Floating particles */}
      {[
        { top: "18%", left: "12%", size: 3, delay: 0 },
        { top: "32%", left: "78%", size: 2, delay: 1.2 },
        { top: "58%", left: "22%", size: 2.5, delay: 2.1 },
        { top: "72%", left: "68%", size: 2, delay: 0.6 },
        { top: "44%", left: "48%", size: 3, delay: 1.8 },
        { top: "85%", left: "40%", size: 2, delay: 2.8 },
      ].map((p, i) => (
        <motion.span
          key={i}
          className="absolute rounded-full bg-accent/70"
          style={{
            top: p.top,
            left: p.left,
            width: p.size,
            height: p.size,
            boxShadow: "0 0 12px rgba(74,222,128,0.55)",
          }}
          animate={{ y: [0, -18, 0], opacity: [0.25, 0.9, 0.25] }}
          transition={{
            duration: 5 + i,
            repeat: Infinity,
            ease: "easeInOut",
            delay: p.delay,
          }}
        />
      ))}

      {/* Soft vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,rgba(9,13,13,0.55)_100%)]" />
    </div>
  );
}
