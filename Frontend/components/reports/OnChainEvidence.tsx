import { Fingerprint, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";

export function OnChainEvidence({ report }: { report: any }) {
  if (!report.ipfs_cid || !report.tx_hash) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass rounded-[2rem] p-6 border-emerald-500/20 bg-emerald-500/[0.02]"
    >
      <div className="flex items-center gap-2 mb-6">
        <div className="p-1.5 rounded-lg bg-emerald-500/10">
          <Fingerprint className="w-4 h-4 text-emerald-400" />
        </div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400">On-Chain Evidence</h3>
      </div>
      <div className="space-y-4">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1.5">PDF Report (IPFS)</p>
          <div className="flex items-center gap-2 bg-black/20 p-2.5 rounded-xl border border-white/5">
            <p className="text-[10px] font-mono text-white/60 truncate flex-1">{report.ipfs_cid}</p>
            <a 
              href={`https://gateway.pinata.cloud/ipfs/${report.ipfs_cid}`} 
              target="_blank" 
              rel="noreferrer" 
              className="flex items-center gap-1.5 px-3 py-1 rounded border border-accent/20 bg-accent/10 text-[10px] font-bold uppercase text-accent hover:bg-accent hover:text-ink transition"
            >
              View PDF <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-white/30 mb-1.5">Base Sepolia Proof</p>
          <div className="flex items-center gap-2 bg-black/20 p-2.5 rounded-xl border border-white/5">
            <p className="text-[10px] font-mono text-white/60 truncate flex-1">{report.tx_hash}</p>
            <a href={`https://base-sepolia.blockscout.com/tx/${report.tx_hash}`} target="_blank" rel="noreferrer" className="text-accent hover:text-white">
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
        <div className="pt-2 text-center">
          <p className="text-[10px] text-white/30 italic">Immutable and verified by Base Sepolia validators.</p>
        </div>
      </div>
    </motion.div>
  );
}
