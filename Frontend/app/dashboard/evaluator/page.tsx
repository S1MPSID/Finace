"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { fetchReports } from "@/store/slices/reportsSlice";
import { CompliancePdfActions } from "@/components/reports/CompliancePdfActions";
import { statusTone } from "@/lib/dashboard/reportTitle";

type StatusFilter = "" | "pending" | "verified" | "rejected";

function formatReportDate(value: unknown): string {
  if (!value) return "—";
  const d = new Date(String(value));
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function EvaluatorDashboard() {
  const dispatch = useAppDispatch();
  const reports = useAppSelector((s) => s.reports.reports);
  const isLoading = useAppSelector((s) => s.reports.isLoading);
  const user = useAppSelector((s) => s.auth.user);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");

  useEffect(() => {
    dispatch(fetchReports());
  }, [dispatch]);

  const filteredReports = statusFilter ? reports.filter((r) => r.status === statusFilter) : reports;
  const tabs: { label: string; value: StatusFilter }[] = [
    { label: "All", value: "" },
    { label: "Pending", value: "pending" },
    { label: "Verified", value: "verified" },
    { label: "Rejected", value: "rejected" },
  ];

  return (
    <div className="space-y-6">
      <div className="glass rounded-[1.8rem] p-6">
        <h2 className="text-2xl font-semibold text-white">Evaluator Console</h2>
        <p className="mt-2 text-sm text-white/60">Review and approve AI-generated compliance reports.</p>
        {user?.role === "evaluator" && (
          <p className="mt-1 text-xs text-accent/70">
            Signed in as <span className="font-semibold text-accent">{user.name}</span>
          </p>
        )}
      </div>

      <div className="glass rounded-[1.8rem] p-6">
        <div className="mb-6 flex flex-wrap gap-2">
          {tabs.map((t) => (
            <button
              key={t.value}
              onClick={() => setStatusFilter(t.value)}
              className={`rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-wider border transition-all ${
                statusFilter === t.value
                  ? "text-accent border-accent/30 bg-white/[0.06]"
                  : "text-white/40 border-white/5 hover:text-white/60"
              }`}
            >
              {t.label} (
              {t.value === "" ? reports.length : reports.filter((r) => r.status === t.value).length})
            </button>
          ))}
        </div>

        {isLoading ? (
          <p className="text-white/50">Loading reports...</p>
        ) : filteredReports.length === 0 ? (
          <p className="text-white/50">No reports found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1080px] border-collapse text-sm text-white/80">
              <thead>
                <tr className="border-b border-white/10 text-xs uppercase tracking-wider text-white/45">
                  <th className="w-[14%] py-3 pr-4 text-left font-medium align-middle">Report ID</th>
                  <th className="w-[17%] px-4 py-3 text-left font-medium align-middle">Date</th>
                  <th className="w-[9%] px-4 py-3 text-center font-medium align-middle">Risk</th>
                  <th className="w-[9%] px-4 py-3 text-center font-medium align-middle">Score</th>
                  <th className="w-[11%] px-4 py-3 text-center font-medium align-middle">Status</th>
                  <th className="w-[40%] py-3 pl-4 text-right font-medium align-middle">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredReports.map((report: any) => (
                  <tr key={report.report_id} className="transition hover:bg-white/[0.02]">
                    <td className="py-4 pr-4 align-middle font-mono text-xs text-white/75">
                      {report.report_id}
                    </td>
                    <td className="px-4 py-4 align-middle text-xs text-white/55 whitespace-nowrap">
                      {formatReportDate(report.created_at || report.updated_at)}
                    </td>
                    <td className="px-4 py-4 align-middle text-center">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase border ${
                          report.risk_level === "HIGH"
                            ? "bg-red-500/10 text-red-400 border-red-500/20"
                            : report.risk_level === "MEDIUM"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                              : "bg-green-500/10 text-green-400 border-green-500/20"
                        }`}
                      >
                        {report.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-4 align-middle text-center font-medium tabular-nums">
                      {report.compliance_score ?? "--"}
                      <span className="text-white/35">/100</span>
                    </td>
                    <td className="px-4 py-4 align-middle text-center">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase ring-1 ring-inset ${statusTone(report.status)}`}
                      >
                        {report.status}
                      </span>
                    </td>
                    <td className="py-4 pl-4 align-middle text-right">
                      <div className="inline-flex flex-nowrap items-center justify-end gap-2">
                        <CompliancePdfActions
                          reportId={report.report_id}
                          isSigned={report.is_digitally_signed}
                          size="sm"
                          compact
                        />
                        <Link
                          href={`/dashboard/evaluator/${report.report_id}`}
                          className="inline-flex shrink-0 items-center rounded-full border border-white/15 bg-white/10 px-4 py-1.5 text-xs font-medium text-white transition hover:bg-white/20 whitespace-nowrap"
                        >
                          Review
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
