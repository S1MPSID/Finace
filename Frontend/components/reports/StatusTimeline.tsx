import { FileText, Clock, CheckCircle2, XCircle, Fingerprint } from "lucide-react";

export function StatusTimeline({ report }: { report: any }) {
  const steps = [
    { label: "Created", done: true, icon: FileText, time: report.created_at },
    { label: "Under Review", done: report.status !== "pending", icon: Clock, time: null },
    {
      label: report.status === "rejected" ? "Rejected" : "Verified",
      done: report.status === "verified" || report.status === "rejected",
      icon: report.status === "rejected" ? XCircle : CheckCircle2,
      time: report.evaluation_metadata?.evaluated_at,
      color: report.status === "rejected" ? "rose" : "emerald",
    },
    { label: "Proof Generated", done: !!(report.ipfs_cid && report.tx_hash), icon: Fingerprint, time: null },
  ];

  return (
    <div className="flex items-start gap-0">
      {steps.map((step, i) => {
        const Icon = step.icon;
        const isActive = step.done;
        const clr = (step as any).color || "accent";
        return (
          <div key={step.label} className="flex flex-col items-center flex-1">
            <div className="flex items-center w-full">
              {i > 0 && <div className={`flex-1 h-px ${isActive ? "bg-white/20" : "bg-white/5"}`} />}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border shrink-0 ${isActive
                ? `bg-${clr === "rose" ? "rose" : clr === "emerald" ? "emerald" : "accent"}-500/20 border-${clr === "rose" ? "rose" : clr === "emerald" ? "emerald" : "accent"}-500/30`
                : "bg-white/5 border-white/10"}`}>
                <Icon className={`w-3.5 h-3.5 ${isActive ? (clr === "rose" ? "text-rose-400" : clr === "emerald" ? "text-emerald-400" : "text-accent") : "text-white/30"}`} />
              </div>
              {i < steps.length - 1 && <div className={`flex-1 h-px ${isActive ? "bg-white/20" : "bg-white/5"}`} />}
            </div>
            <div className="mt-2 text-center px-1">
              <p className={`text-xs font-medium ${isActive ? "text-white" : "text-white/30"}`}>{step.label}</p>
              {step.time && <p className="text-[10px] text-white/30 mt-0.5">{new Date(step.time).toLocaleString()}</p>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
