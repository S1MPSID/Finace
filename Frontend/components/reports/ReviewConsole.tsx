import { Loader2 } from "lucide-react";

interface ReviewConsoleProps {
  remarks: string;
  setRemarks: (val: string) => void;
  submitting: boolean;
  actionType: string | null;
  handleReview: (status: "verified" | "rejected") => void;
}

export function ReviewConsole({ remarks, setRemarks, submitting, actionType, handleReview }: ReviewConsoleProps) {
  return (
    <div className="glass rounded-[2rem] p-6 border-white/10">
      <h3 className="text-xs font-bold uppercase tracking-wider text-white/40 mb-6">Review Console</h3>
      <textarea
        className="w-full bg-white/[0.03] border border-white/10 rounded-2xl p-4 text-sm text-white focus:outline-none focus:ring-1 focus:ring-accent/40 transition mb-4 min-h-[120px] placeholder:text-white/20 resize-none [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        placeholder="Submit your expert remarks here..."
        value={remarks}
        onChange={(e) => setRemarks(e.target.value)}
        disabled={submitting}
      />
      <div className="flex gap-3">
        <button
          onClick={() => handleReview("verified")}
          disabled={submitting}
          className="flex-1 rounded-2xl bg-accent text-ink py-3 text-sm font-bold transition hover:bg-white disabled:opacity-50"
        >
          {actionType === "verified" ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Verify"}
        </button>
        <button
          onClick={() => handleReview("rejected")}
          disabled={submitting}
          className="flex-1 rounded-2xl bg-white/5 border border-white/10 py-3 text-sm font-bold text-white hover:bg-rose-500/20 hover:border-rose-500/30 transition disabled:opacity-50"
        >
          {actionType === "rejected" ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Reject"}
        </button>
      </div>
    </div>
  );
}
