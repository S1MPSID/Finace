"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BrainCircuit,
  ShieldCheck,
  GitBranch,
  Target,
  FlaskConical,
  Scale,
  Users,
  ChevronRight,
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { mlValidationApi } from "@/services/api";
import { ConfusionMatrix } from "@/components/ml-validation/ConfusionMatrix";
import { FeatureImportanceBars } from "@/components/ml-validation/FeatureImportanceBars";
import { CaseDetailPanel } from "@/components/ml-validation/CaseDetailPanel";
import { ACCENT_HEX } from "@/lib/theme/colors";

type DashboardPayload = any;

const SECTIONS = [
  { id: "overview", label: "Overview", icon: BrainCircuit },
  { id: "pipeline", label: "Pipeline", icon: GitBranch },
  { id: "performance", label: "Model Performance", icon: Target },
  { id: "robustness", label: "Robustness Testing", icon: FlaskConical },
  { id: "grounding", label: "Regulatory Grounding", icon: ShieldCheck },
  { id: "compare", label: "ML vs Finace", icon: Scale },
  { id: "human", label: "Human Validation", icon: Users },
] as const;

export default function MLValidationPage() {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<(typeof SECTIONS)[number]["id"]>("overview");

  const [robustCases, setRobustCases] = useState<any[]>([]);
  const [compareCases, setCompareCases] = useState<any[]>([]);
  const [humanCases, setHumanCases] = useState<any[]>([]);
  const [casesLoading, setCasesLoading] = useState(false);
  const [selected, setSelected] = useState<any | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res: any = await mlValidationApi.dashboard();
        if (!cancelled) setData(res);
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.response?.data?.error || e?.message || "Failed to load ML validation dashboard");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const loadCases = useCallback(async (setName: "robustness" | "human" | "comparison") => {
    setCasesLoading(true);
    try {
      const res: any = await mlValidationApi.cases({ set: setName, limit: 12, offset: 0 });
      const rows = res?.cases || [];
      if (setName === "robustness") setRobustCases(rows);
      if (setName === "comparison") setCompareCases(rows);
      if (setName === "human") setHumanCases(rows);
      if (rows[0]) setSelected(rows[0]);
    } catch {
      /* keep prior */
    } finally {
      setCasesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (active === "robustness" || active === "grounding") {
      if (!robustCases.length) void loadCases("robustness");
    }
    if (active === "compare" && !compareCases.length) void loadCases("comparison");
    if (active === "human" && !humanCases.length) void loadCases("human");
  }, [active, robustCases.length, compareCases.length, humanCases.length, loadCases]);

  const overview = data?.overview;
  const performance = data?.performance;
  const robustness = data?.robustness;
  const compare = data?.ml_vs_finace;
  const human = data?.human_validation;

  const domainChart = useMemo(() => {
    const map = performance?.per_domain_status_accuracy || {};
    return Object.entries(map).map(([domain, acc]) => ({
      domain,
      accuracy: Math.round(Number(acc) * 1000) / 10,
    }));
  }, [performance]);

  const metricCards = [
    { label: "Current Model", value: overview?.current_model || "—" },
    {
      label: "Compliance Scenarios",
      value: overview?.compliance_scenarios?.toLocaleString?.() || "—",
    },
    { label: "Main Test Accuracy", value: overview?.main_test_accuracy_display || "—" },
    {
      label: "Unseen Requirement Accuracy",
      value: overview?.unseen_requirement_accuracy_display || "—",
    },
    { label: "Robustness Test", value: overview?.robustness_accuracy_display || "—" },
    {
      label: "Human Validation",
      value:
        overview?.human_validation_cases != null
          ? `${overview.human_validation_cases} Cases`
          : "—",
    },
  ];

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-3 text-white/50">
        <Loader2 className="h-5 w-5 animate-spin text-accent" />
        Loading ML Validation…
      </div>
    );
  }

  if (error || !data?.available) {
    return (
      <div className="glass rounded-[1.8rem] p-8 max-w-2xl">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-amber-300 shrink-0 mt-0.5" />
          <div>
            <h1 className="text-xl font-semibold text-white">ML Validation</h1>
            <p className="mt-2 text-sm text-white/55">
              {error ||
                "ML validation artifacts are not available. Ensure the Python RAG service is running and the current model has been trained."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 pb-10">
      <header className="glass rounded-[1.8rem] p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent/80">
              Independent validation
            </p>
            <h1 className="mt-2 text-2xl sm:text-3xl font-semibold tracking-tight text-white">
              ML Validation
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-white/55 leading-6">
              Independent machine learning validation of Finace compliance assessments.
            </p>
          </div>
          <div className="rounded-2xl border border-accent/25 bg-accent/10 px-4 py-3">
            <p className="text-[10px] uppercase tracking-wider text-accent/70">Current Model</p>
            <p className="text-lg font-semibold text-accent">{overview?.current_model}</p>
          </div>
        </div>
        <p className="mt-5 rounded-2xl border border-white/8 bg-black/20 px-4 py-3 text-[13px] leading-6 text-white/60">
          {data.architecture_note}
        </p>
      </header>

      <nav className="flex gap-1.5 overflow-x-auto pb-1" style={{ scrollbarWidth: "thin" }}>
        {SECTIONS.map((s) => {
          const Icon = s.icon;
          const on = active === s.id;
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => setActive(s.id)}
              className={`flex shrink-0 items-center gap-2 rounded-full border px-3.5 py-2 text-[12px] transition ${
                on
                  ? "border-accent/30 bg-accent/12 text-accent"
                  : "border-white/8 bg-white/[0.03] text-white/50 hover:text-white/80"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {s.label}
            </button>
          );
        })}
      </nav>

      {active === "overview" && (
        <section className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {metricCards.map((card) => (
              <div key={card.label} className="glass rounded-[1.4rem] p-5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">
                  {card.label}
                </p>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-white">{card.value}</p>
              </div>
            ))}
          </div>

          <div className="glass rounded-[1.4rem] p-6">
            <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-white/40">
              How Finace and ML work together
            </h2>
            <div className="mt-4 grid gap-3 md:grid-cols-3 text-sm">
              <ArchCard
                title="Regulatory Source"
                body="Documents and retrieved clauses remain the source of truth."
              />
              <ArchCard
                title="Finace Engine"
                body="RAG, deterministic rules, and Gemini produce the primary compliance assessment."
              />
              <ArchCard
                title="ML Validation"
                body="An independent prediction used as a validation signal — never a replacement."
              />
            </div>
          </div>
        </section>
      )}

      {active === "pipeline" && (
        <section className="glass rounded-[1.4rem] p-6">
          <h2 className="text-lg font-semibold text-white">ML Pipeline</h2>
          <p className="mt-1 text-sm text-white/50">
            From regulatory sources to an independent compliance prediction.
          </p>
          <ol className="mt-6 space-y-3">
            {(data.pipeline_steps || []).map((step: any, idx: number) => (
              <li
                key={step.title}
                className="flex gap-3 rounded-2xl border border-white/8 bg-white/[0.03] p-4"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-accent/25 bg-accent/10 text-xs font-semibold text-accent">
                  {idx + 1}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-white/90">{step.title}</p>
                    {idx < (data.pipeline_steps?.length || 0) - 1 && (
                      <ChevronRight className="h-3.5 w-3.5 text-white/25" />
                    )}
                  </div>
                  <p className="mt-1 text-sm text-white/50">{step.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {active === "performance" && (
        <section className="space-y-4">
          <div className="glass rounded-[1.4rem] p-6">
            <h2 className="text-lg font-semibold text-white">Model Performance</h2>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[520px] text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-left text-[11px] uppercase tracking-wider text-white/35">
                    <th className="py-2 pr-4 font-medium">Metric</th>
                    <th className="py-2 font-medium">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {(performance?.metrics || [])
                    .filter((m: any) =>
                      [
                        "main_test_accuracy",
                        "unseen_requirement_accuracy",
                        "robustness_accuracy",
                        "calibration_error",
                      ].includes(m.key)
                    )
                    .map((m: any) => (
                      <tr key={m.key} className="border-b border-white/5">
                        <td className="py-3 pr-4">
                          <p className="text-white/85">{m.label}</p>
                          <p className="mt-1 text-[12px] text-white/40 max-w-xl">{m.explanation}</p>
                        </td>
                        <td className="py-3 text-lg font-semibold tabular-nums text-accent">
                          {m.display ?? "—"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
            <div className="mt-4 space-y-2 text-[13px] text-white/50 leading-6">
              <p>
                {overview?.main_test_accuracy_display} accuracy means the model correctly classified
                approximately{" "}
                {overview?.main_test_accuracy != null
                  ? Math.round(overview.main_test_accuracy * 100)
                  : "97"}{" "}
                out of every 100 cases in the held-out test set.
              </p>
              <p>
                {overview?.unseen_requirement_accuracy_display} unseen requirement accuracy measures
                how well the model generalizes to requirements not directly represented in training.
              </p>
              <p>
                {overview?.robustness_accuracy_display} robustness accuracy comes from deliberately
                difficult cases designed to reduce simple keyword-based shortcuts.
              </p>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="glass rounded-[1.4rem] p-6">
              <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-white/40">
                Confusion Matrix
              </h3>
              <div className="mt-4">
                <ConfusionMatrix
                  labels={performance?.confusion_matrix?.labels}
                  matrix={performance?.confusion_matrix?.matrix}
                />
              </div>
            </div>
            <div className="glass rounded-[1.4rem] p-6">
              <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-white/40">
                Feature Importance
              </h3>
              <div className="mt-4">
                <FeatureImportanceBars features={performance?.feature_importance} />
              </div>
            </div>
          </div>

          {domainChart.length > 0 && (
            <div className="glass rounded-[1.4rem] p-6">
              <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-white/40">
                Per-domain accuracy
              </h3>
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={domainChart} margin={{ left: 0, right: 8, top: 8, bottom: 24 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis
                      dataKey="domain"
                      tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }}
                      angle={-25}
                      textAnchor="end"
                      height={50}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }}
                      unit="%"
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#0f1715",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: 12,
                      }}
                      formatter={(value) => [`${value ?? 0}%`, "Accuracy"]}
                    />
                    <Bar dataKey="accuracy" fill={ACCENT_HEX} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </section>
      )}

      {active === "robustness" && (
        <section className="space-y-4">
          <div className="glass rounded-[1.4rem] p-6">
            <h2 className="text-lg font-semibold text-white">Robustness Testing</h2>
            <p className="mt-2 text-sm text-white/55 leading-6">{robustness?.explanation}</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <StatTile label="Robustness Test Cases" value={robustness?.n_cases ?? "—"} />
              <StatTile label="Accuracy" value={robustness?.accuracy_display ?? "—"} />
            </div>
          </div>
          <CaseBrowser
            title="Inspect robustness cases"
            cases={robustCases}
            loading={casesLoading}
            selectedId={selected?.case_id}
            onSelect={setSelected}
            mode="robustness"
          />
        </section>
      )}

      {active === "grounding" && (
        <section className="space-y-4">
          <div className="glass rounded-[1.4rem] p-6">
            <h2 className="text-lg font-semibold text-white">Regulatory Grounding</h2>
            <p className="mt-2 text-sm text-white/55 leading-6">
              Regulatory Source → Requirement → Scenario → Expected Outcome → ML Prediction
            </p>
            <p className="mt-3 text-[13px] text-white/40">
              Regulatory evidence is visually separated from the ML prediction so examiners can see
              that the model is not generating regulatory truth.
            </p>
          </div>
          <CaseBrowser
            title="Grounded cases"
            cases={robustCases}
            loading={casesLoading}
            selectedId={selected?.case_id}
            onSelect={setSelected}
            mode="grounding"
          />
        </section>
      )}

      {active === "compare" && (
        <section className="space-y-4">
          <div className="glass rounded-[1.4rem] p-6">
            <h2 className="text-lg font-semibold text-white">ML vs Finace</h2>
            <p className="mt-2 text-sm text-white/55 leading-6">
              How the independent ML validation signal compares with the existing Finace compliance
              engine (deterministic rules baseline in this comparison).
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <StatTile label="Cases compared" value={compare?.n_compared ?? "—"} />
              <StatTile
                label="ML vs rules risk agreement"
                value={
                  compare?.ml_vs_rules_risk_agreement != null
                    ? `${(compare.ml_vs_rules_risk_agreement * 100).toFixed(0)}%`
                    : "—"
                }
              />
              <StatTile
                label="Disagreements"
                value={compare?.risk_disagreement?.n_disagree ?? "—"}
              />
            </div>
            {compare?.risk_disagreement?.pairs && (
              <div className="mt-5">
                <p className="text-[11px] uppercase tracking-wider text-white/35">
                  Disagreement pairs
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(compare.risk_disagreement.pairs).map(([pair, n]) => (
                    <span
                      key={pair}
                      className="rounded-full border border-amber-400/25 bg-amber-500/10 px-3 py-1 text-[11px] text-amber-200"
                    >
                      {String(pair).replace(/__/g, " / ").replace(/_/g, " ")}: {String(n)}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <p className="mt-4 text-[13px] text-white/45 leading-6">{compare?.note}</p>
          </div>
          <CaseBrowser
            title="Comparison samples"
            cases={compareCases}
            loading={casesLoading}
            selectedId={selected?.case_id}
            onSelect={setSelected}
            mode="comparison"
          />
        </section>
      )}

      {active === "human" && (
        <section className="space-y-4">
          <div className="glass rounded-[1.4rem] p-6">
            <h2 className="text-lg font-semibold text-white">Human Validation</h2>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <StatTile
                label="Cases Reserved for Human Validation"
                value={human?.n_cases ?? "—"}
              />
              <StatTile
                label="Review Status"
                value={
                  human?.pending
                    ? "Pending Human Review"
                    : (human?.review_status || "—").replace(/_/g, " ")
                }
              />
            </div>
            {human?.pending && (
              <p className="mt-4 rounded-xl border border-amber-400/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-100/90">
                Pending Human Review — accuracy is not shown until cases are independently approved.
              </p>
            )}
            {human?.metrics_available && human?.metrics?.status_accuracy != null && (
              <p className="mt-4 text-sm text-white/60">
                Approved-subset accuracy:{" "}
                <span className="text-accent font-semibold">
                  {(human.metrics.status_accuracy * 100).toFixed(1)}%
                </span>{" "}
                (n={human.metrics.n})
              </p>
            )}
            <p className="mt-3 text-[13px] text-white/45">{human?.note}</p>
          </div>
          <CaseBrowser
            title="Human validation cases"
            cases={humanCases}
            loading={casesLoading}
            selectedId={selected?.case_id}
            onSelect={setSelected}
            mode="human"
          />
        </section>
      )}
    </div>
  );
}

function ArchCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-accent/80">{title}</p>
      <p className="mt-2 text-white/55 leading-6">{body}</p>
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-4">
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

function CaseBrowser({
  title,
  cases,
  loading,
  selectedId,
  onSelect,
  mode,
}: {
  title: string;
  cases: any[];
  loading: boolean;
  selectedId?: string;
  onSelect: (c: any) => void;
  mode: "grounding" | "robustness" | "comparison" | "human";
}) {
  const selected = cases.find((c) => c.case_id === selectedId) || cases[0] || null;

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
      <div className="glass rounded-[1.4rem] p-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-white/80">{title}</h3>
          {loading && <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" />}
        </div>
        <div className="max-h-[520px] space-y-1.5 overflow-y-auto pr-1" style={{ scrollbarWidth: "thin" }}>
          {!loading && cases.length === 0 && (
            <p className="text-sm text-white/40">No cases available.</p>
          )}
          {cases.map((c) => {
            const on = c.case_id === selected?.case_id;
            return (
              <button
                key={c.case_id}
                type="button"
                onClick={() => onSelect(c)}
                className={`w-full rounded-xl border px-3 py-2.5 text-left transition ${
                  on
                    ? "border-accent/30 bg-accent/10"
                    : "border-white/8 bg-white/[0.02] hover:bg-white/[0.04]"
                }`}
              >
                <p className="truncate text-[12px] font-medium text-white/80">{c.case_id}</p>
                <p className="mt-0.5 truncate text-[11px] text-white/40">
                  {c.domain || "—"} · {(c.expected_status || "—").replace(/_/g, " ")}
                </p>
              </button>
            );
          })}
        </div>
      </div>
      <div className="glass rounded-[1.4rem] p-5">
        <CaseDetailPanel caseRow={selected} mode={mode} />
      </div>
    </div>
  );
}
