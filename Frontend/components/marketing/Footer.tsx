import { ShieldCheck } from "lucide-react";
import { ACCENT_RGB } from "@/lib/theme/colors";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] bg-[#090d0d]">
      <div className="shell relative z-10 flex flex-wrap items-center justify-between gap-4 py-8">
        <div className="flex items-center gap-2 text-sm text-white/50">
          <ShieldCheck className="h-4 w-4 text-accent" />
          <span className="font-semibold text-accent">Finace</span>
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

      <div className="relative h-44 overflow-hidden sm:h-56 md:h-64 lg:h-80">
        <div className="pointer-events-none absolute bottom-[-6%] left-0 flex w-full select-none justify-center">
          <span
            className="whitespace-nowrap text-[24vw] font-bold leading-none tracking-tighter sm:text-[22vw] md:text-[20vw] lg:text-[18vw]"
            style={{
              color: `rgb(${ACCENT_RGB})`,
              opacity: 0.22,
              maskImage: "linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.4) 25%, black 55%)",
              WebkitMaskImage: "linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.4) 25%, black 55%)",
            }}
            aria-hidden
          >
            Finace
          </span>
        </div>
      </div>
    </footer>
  );
}
