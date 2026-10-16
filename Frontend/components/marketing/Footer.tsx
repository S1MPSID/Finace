import { ShieldCheck } from "lucide-react";

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
