import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Fingerprint, Loader2, CheckCircle2, AlertCircle, FileText, ExternalLink } from "lucide-react";

interface ProofGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (orgName: string) => Promise<void>;
  status: "idle" | "generating" | "success" | "error";
  txHash: string | null;
  ipfsCid: string | null;
  error: string | null;
}

export function ProofGenerationModal({
  isOpen,
  onClose,
  onGenerate,
  status,
  txHash,
  ipfsCid,
  error,
}: ProofGenerationModalProps) {
  const [orgName, setOrgName] = useState("");

  // Reset state when opened
  useEffect(() => {
    if (isOpen && status === "idle") {
      setOrgName("Acme Fintech");
    }
  }, [isOpen, status]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={() => status !== "generating" && onClose()}
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-md overflow-hidden rounded-[2rem] border border-white/10 bg-[#0d1413] p-6 shadow-2xl sm:p-8"
        >
          {/* Close Button */}
          {status !== "generating" && (
            <button
              onClick={onClose}
              className="absolute right-4 top-4 rounded-full p-2 text-white/40 transition hover:bg-white/10 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          )}

          <div className="mb-6 flex items-center gap-3">
            <div className={`flex h-12 w-12 items-center justify-center rounded-2xl border ${status === "success" ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : status === "error" ? "bg-rose-500/10 border-rose-500/20 text-rose-400" : "bg-accent/10 border-accent/20 text-accent"}`}>
              {status === "success" ? <CheckCircle2 className="w-6 h-6" /> : status === "error" ? <AlertCircle className="w-6 h-6" /> : <Fingerprint className="w-6 h-6" />}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Generate Audit Proof</h2>
              <p className="text-xs text-white/50">Anchor compliance report to Base Sepolia</p>
            </div>
          </div>

          {/* Input State */}
          {status === "idle" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div>
                <label className="mb-2 block text-sm font-medium text-white/70">Organization Name</label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white focus:border-accent/40 focus:outline-none focus:ring-1 focus:ring-accent/40"
                  placeholder="e.g. Acme Fintech Pvt Ltd"
                />
              </div>

              <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 text-xs leading-relaxed text-white/40">
                This will generate a formal PDF report, upload it immutably to IPFS, and write the document hash to the Base Sepolia blockchain.
              </div>

              <button
                onClick={() => orgName.trim() && onGenerate(orgName.trim())}
                disabled={!orgName.trim()}
                className="w-full rounded-2xl bg-accent py-3.5 text-sm font-bold text-ink transition hover:bg-white disabled:opacity-50"
              >
                Start Generation
              </button>
            </motion.div>
          )}

          {/* Generating State */}
          {status === "generating" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 py-4">
              <div className="flex flex-col items-center justify-center gap-4 text-center">
                <Loader2 className="w-10 h-10 animate-spin text-accent" />
                <div>
                  <p className="text-sm font-semibold text-white">Processing Blockchain Proof...</p>
                  <p className="mt-1 text-xs text-white/50">Please wait, this may take up to 30 seconds.</p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm text-white/70">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Generating PDF Report...
                </div>
                <div className="flex items-center gap-3 text-sm text-white/70">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Uploading to IPFS...
                </div>
                <div className="flex items-center gap-3 text-sm text-white/70 animate-pulse">
                  <Loader2 className="w-4 h-4 animate-spin text-accent" /> Waiting for MetaMask Signing...
                </div>
              </div>
            </motion.div>
          )}

          {/* Success State */}
          {status === "success" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-center">
                <p className="text-sm font-medium text-emerald-400">Proof anchored successfully!</p>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1.5">PDF Report</p>
                  <a
                    href={`https://gateway.pinata.cloud/ipfs/${ipfsCid}`}
                    target="_blank"
                    rel="noreferrer"
                    className="group flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.05] p-3 transition hover:border-accent/40 hover:bg-white/[0.08]"
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-accent" />
                      <span className="text-sm font-medium text-white group-hover:text-accent transition">View PDF</span>
                    </div>
                    <ExternalLink className="w-4 h-4 text-white/40 group-hover:text-white" />
                  </a>
                </div>

                <div>
                  <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1.5">Transaction Hash</p>
                  <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-black/20 p-3">
                    <p className="flex-1 truncate font-mono text-xs text-white/60">{txHash}</p>
                  </div>
                </div>
              </div>

              <button
                onClick={onClose}
                className="w-full rounded-2xl bg-white/10 py-3 text-sm font-semibold text-white transition hover:bg-white/20"
              >
                Close
              </button>
            </motion.div>
          )}

          {/* Error State */}
          {status === "error" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4">
                <p className="text-sm font-medium text-rose-400 text-center mb-2">Generation Failed</p>
                <p className="text-xs text-rose-400/70 text-center">{error}</p>
              </div>

              <button
                onClick={onClose}
                className="w-full rounded-2xl bg-white/10 py-3 text-sm font-semibold text-white transition hover:bg-white/20"
              >
                Dismiss
              </button>
            </motion.div>
          )}

        </motion.div>
      </div>
    </AnimatePresence>
  );
}
