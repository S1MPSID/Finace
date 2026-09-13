"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  FileText,
  Fingerprint,
  Loader2,
  MessageSquare,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { RadialBar, RadialBarChart, PolarAngleAxis, ResponsiveContainer } from "recharts";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { fetchReports } from "@/store/slices/reportsSlice";
import { ACCENT_HEX, ACCENT_RGB } from "@/lib/theme/colors";
import { reportDisplayTitle, riskTone, statusTone } from "@/lib/dashboard/reportTitle";

function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  accent,
  chart,
}: {
  icon: typeof Activity;
  label: string;
  value: string;
  hint: string;
  accent: string;
  chart?: React.ReactNode;
}) {
  return (
    <div className={`glass group rounded-2xl p-5 transition duration-300 hover:shadow-[0_16px_48px_-20px_rgba(${ACCENT_RGB},0.14)]`}>
      <div className="relative z-[1] flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className={`mb-4 inline-flex rounded-xl p-2.5 ring-1 ring-inset ${accent}`}>
            <Icon className="h-4 w-4" />
          </div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/38">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight text-white">{value}</p>
          <p className="mt-1.5 text-xs text-white/42">{hint}</p>
        </div>
        {chart && <div className="h-16 w-16 shrink-0 opacity-90">{chart}</div>}
      </div>
    </div>
  );
}

export function OverviewPanel() {
  const dispatch = useAppDispatch();
  const reports = useAppSelector((s) => s.reports.reports);
  const auditLogs = useAppSelector((s) => s.reports.auditLogs);
  const isLoading = useAppSelector((s) => s.reports.isLoading);
  const error = useAppSelector((s) => s.reports.error);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    dispatch(fetchReports());
  }, [dispatch]);

  const totalReports = reports.length;
  const verifiedProofs = auditLogs.length;
  const avgScore =
    totalReports > 0
      ? Math.round(reports.reduce((acc, r) => acc + (r.compliance_score || 0), 0) / totalReports)
      : 0;

  const activeRisks = useMemo(() => {
    let count = 0;
    reports.forEach((r) => {
      if (r.status !== "verified") count += (r.risk_flags || []).length;
    });
    return count;
  }, [reports]);

  const recentReport = reports[0] || null;
  const recentTitle = recentReport ? reportDisplayTitle(recentReport) : null;
  const riskFlags = recentReport?.risk_flags?.slice(0, 4) || [];

  const scoreChart = [{ name: "Score", value: avgScore, fill: ACCENT_HEX }];

  if (isLoading) {
    return (
      <div className="flex min-h-[420px] flex-col items-center justify-center text-white/50">
        <Loader2 className="mb-4 h-8 w-8 animate-spin text-accent" />
        <p className="text-sm">Loading dashboard…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass rounded-2xl border-rose-500/15 bg-rose-500/[0.04] p-8 text-rose-200">
        <h3 className="text-lg font-semibold">Could not load reports</h3>
        <p className="mt-2 text-sm opacity-80">{error}</p>
        <button
          type="button"
          onClick={() => dispatch(fetchReports())}
          className="mt-4 rounded-xl bg-rose-500/20 px-4 py-2 text-sm hover:bg-rose-500/30"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="relative mx-auto max-w-6xl space-y-8">
      <div className="pointer-events-none absolute -top-20 left-1/4 h-48 w-96 -translate-x-1/2 rounded-full bg-accent/8 blur-[80px]" />

      <header className="relative flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent/75">Dashboard</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-[2rem]">Overview</h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/48">
            Compliance scores, open risks, and report status — synced from your workspace.
          </p>
        </div>
        <Link
          href="/dashboard/workflow"
          className={`inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-ink shadow-[0_8px_24px_-8px_rgba(${ACCENT_RGB},0.45)] transition hover:bg-white hover:shadow-[0_8px_28px_-6px_rgba(255,255,255,0.2)]`}
        >
          <Sparkles className="h-4 w-4" />
          New analysis
        </Link>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={Activity}
          label="Avg compliance"
          value={`${avgScore}`}
          hint={`Across ${totalReports} report${totalReports === 1 ? "" : "s"}`}
          accent="bg-accent/10 text-accent ring-accent/20"
          chart={
            mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  cx="50%"
                  cy="50%"
                  innerRadius="68%"
                  outerRadius="100%"
                  barSize={7}
                  data={scoreChart}
                  startAngle={90}
                  endAngle={-270}
                >
                  <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                  <RadialBar
                    background={{ fill: "rgba(255,255,255,0.05)" }}
                    dataKey="value"
                    cornerRadius={8}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
            ) : null
          }
        />
        <StatCard
          icon={ShieldAlert}
          label="Active risks"
          value={String(activeRisks)}
          hint="In pending workflows"
          accent="bg-amber-500/10 text-amber-300 ring-amber-400/20"
        />
        <StatCard
          icon={FileText}
          label="Reports"
          value={String(totalReports)}
          hint="Generated this session"
          accent="bg-sky-500/10 text-sky-300 ring-sky-400/20"
        />
        <StatCard
          icon={CheckCircle2}
          label="On-chain proofs"
          value={String(verifiedProofs)}
          hint="Base Sepolia anchors"
          accent="bg-emerald-500/10 text-emerald-300 ring-emerald-400/20"
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-6"
        >
          <div className="relative z-[1]">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/38">
                  Latest report
                </p>
                {recentReport ? (
                  <>
                    <h2 className="mt-2 text-xl font-semibold leading-snug text-white">{recentTitle}</h2>
                    <p className="mt-1 font-mono text-xs text-white/32">{recentReport.report_id}</p>
                  </>
                ) : (
                  <h2 className="mt-2 text-xl font-semibold text-white">No reports yet</h2>
                )}
              </div>
              {recentReport && (
                <span
                  className={`shrink-0 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider ring-1 ring-inset ${statusTone(recentReport.status)}`}
                >
                  {recentReport.status}
                </span>
              )}
            </div>

            {recentReport ? (
              <>
                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  {[
                    {
                      label: "Score",
                      value: (
                        <>
                          {recentReport.compliance_score ?? "—"}
                          <span className="text-sm text-white/32">/100</span>
                        </>
                      ),
                    },
                    { label: "Risk", value: recentReport.risk_level || "—" },
                    {
                      label: "Regulator",
                      value: recentReport.workflow_input?.regulator || recentReport.regulator || "RBI",
                    },
                  ].map((cell) => (
                    <div key={cell.label} className="panel-inset px-4 py-3">
                      <p className="text-[10px] uppercase tracking-wider text-white/38">{cell.label}</p>
                      <p className="mt-1 text-lg font-semibold text-white">{cell.value}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  <Link
                    href={`/dashboard/evaluator/${recentReport.report_id}`}
                    className={`inline-flex items-center gap-1.5 rounded-full bg-accent px-4 py-2 text-sm font-semibold text-ink shadow-[0_6px_20px_-8px_rgba(${ACCENT_RGB},0.5)] hover:bg-white`}
                  >
                    Open report <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                  {recentReport.chat_id && (
                    <Link
                      href={`/dashboard/workflow?chat=${recentReport.chat_id}`}
                      className="panel-inset inline-flex items-center gap-1.5 px-4 py-2 text-sm text-white/72 transition hover:text-white"
                    >
                      <MessageSquare className="h-3.5 w-3.5" />
                      View chat
                    </Link>
                  )}
                </div>
              </>
            ) : (
              <div className="panel-inset mt-6 px-6 py-10 text-center">
                <FileText className="mx-auto mb-3 h-8 w-8 text-white/18" />
                <p className="text-sm text-white/48">Run an analysis in Compliance Studio, then generate a report.</p>
                <Link
                  href="/dashboard/workflow"
                  className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-accent hover:text-white"
                >
                  Go to Compliance Studio <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            )}
          </div>
        </motion.div>

        <div className="space-y-4">
          <div className="glass rounded-2xl p-5">
            <div className="relative z-[1]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/38">Quick actions</p>
              <div className="mt-4 space-y-2">
                {(
                  [
                    { href: "/dashboard/workflow" as const, label: "Compliance Studio", icon: MessageSquare },
                    { href: "/dashboard/regulations" as const, label: "Regulation library", icon: FileText },
                    { href: "/dashboard/evaluator" as const, label: "Evaluator queue", icon: ShieldAlert },
                  ] as const
                ).map(({ href, label, icon: Icon }) => (
                  <Link
                    key={href}
                    href={href}
                    className="panel-inset flex items-center justify-between px-4 py-3 text-sm text-white/72 transition hover:text-white"
                  >
                    <span className="flex items-center gap-2.5">
                      <Icon className="h-4 w-4 text-accent/65" />
                      {label}
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 text-white/22" />
                  </Link>
                ))}
              </div>
            </div>
          </div>

          <div className="panel-accent rounded-2xl p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-accent/85">Document studio</p>
            <h3 className="mt-2 text-lg font-semibold text-white">Generate legal docs</h3>
            <p className="mt-2 text-sm leading-relaxed text-white/52">
              Turn workflows into privacy policies and terms of service.
            </p>
            <Link
              href="/dashboard/documents"
              className="mt-4 inline-block rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-white ring-1 ring-inset ring-white/12 transition hover:bg-white/14"
            >
              Open studio
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="glass rounded-2xl p-6">
          <div className="relative z-[1]">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/38">Risk flags</p>
                <h2 className="mt-1 text-lg font-semibold text-white">Latest findings</h2>
              </div>
              {recentReport && (
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ring-1 ring-inset ${riskTone(recentReport.risk_level)}`}
                >
                  {recentReport.risk_level || "—"}
                </span>
              )}
            </div>
            {riskFlags.length === 0 ? (
              <p className="panel-inset px-4 py-8 text-center text-sm text-white/38">
                No risk flags on the latest report.
              </p>
            ) : (
              <ul className="space-y-2">
                {riskFlags.map((risk: string) => (
                  <li
                    key={risk}
                    className="panel-inset flex gap-3 px-4 py-3 text-sm leading-relaxed text-white/68"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-400/90 shadow-[0_0_8px_rgba(251,113,133,0.5)]" />
                    {risk}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="relative z-[1]">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/38">Audit trail</p>
                <h2 className="mt-1 text-lg font-semibold text-white">Recent proofs</h2>
              </div>
              <Fingerprint className="h-5 w-5 text-accent/45" />
            </div>
            {auditLogs.length === 0 ? (
              <p className="panel-inset px-4 py-8 text-center text-sm text-white/38">
                No blockchain anchors yet. Verify a report and generate proof.
              </p>
            ) : (
              <ul className="space-y-3">
                {auditLogs.slice(0, 3).map((entry) => (
                  <li key={entry.report_id} className="panel-inset px-4 py-3">
                    <p className="text-sm font-medium text-white/78">Report anchored</p>
                    <p className="mt-1 truncate font-mono text-xs text-white/32">{entry.tx_hash}</p>
                  </li>
                ))}
              </ul>
            )}
            {auditLogs.length > 0 && (
              <Link href="/dashboard/audit" className="mt-4 inline-block text-xs font-medium text-accent hover:text-white">
                View full ledger →
              </Link>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
