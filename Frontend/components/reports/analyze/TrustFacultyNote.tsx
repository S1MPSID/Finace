import type { TrustAnalytics } from "@/lib/trust/types";

export function TrustFacultyNote({ stats }: { stats: TrustAnalytics }) {
  return (
    <section className="rounded-2xl border border-accent/20 bg-accent/5 p-5">
      <h3 className="text-sm font-medium text-accent">Why faculty can trust this path</h3>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-white/65">
        <li>
          <strong className="text-white/85">Evidence-backed:</strong> answers cite retrieved regulatory chunks.
        </li>
        <li>
          <strong className="text-white/85">Explainable:</strong> SHAP/LIME attribute each score to rules and controls.
        </li>
        <li>
          <strong className="text-white/85">Auditable progress:</strong> score trajectory shows remediations (Δ {stats.delta >= 0 ? "+" : ""}{stats.delta}).
        </li>
        <li>
          <strong className="text-white/85">Hybrid decisioning:</strong> rules + RAG + LLM with surrogate fidelity tracking.
        </li>
      </ul>
    </section>
  );
}
