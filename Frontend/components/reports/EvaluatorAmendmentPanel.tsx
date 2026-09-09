"use client";

import { useEffect, useState } from "react";
import { FileText, Loader2, Plus, Save } from "lucide-react";
import { reportsApi } from "@/services/api";
import { htmlToPlainText, plainLinesFromField } from "@/lib/text/htmlToPlain";
import { useDocCatalog } from "@/hooks/useDocCatalog";
import { RegulatoryDocumentPicker } from "@/components/reports/RegulatoryDocumentPicker";

type Props = {
  report: any;
  onSaved: () => void;
  disabled?: boolean;
};

const textareaClass =
  "w-full rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm leading-relaxed text-white resize-y";

export function EvaluatorAmendmentPanel({ report, onSaved, disabled }: Props) {
  const { catalog, loading: docsLoading } = useDocCatalog();
  const [score, setScore] = useState(String(report.compliance_score ?? ""));
  const [risk, setRisk] = useState(report.risk_level || "MEDIUM");
  const [explanation, setExplanation] = useState(htmlToPlainText(report.explanation || ""));
  const [flags, setFlags] = useState(plainLinesFromField(report.risk_flags));
  const [recs, setRecs] = useState(plainLinesFromField(report.recommendations));
  const [comment, setComment] = useState("");
  const [refName, setRefName] = useState("");
  const [refText, setRefText] = useState("");
  const [refComment, setRefComment] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setScore(String(report.compliance_score ?? ""));
    setRisk(report.risk_level || "MEDIUM");
    setExplanation(htmlToPlainText(report.explanation || ""));
    setFlags(plainLinesFromField(report.risk_flags));
    setRecs(plainLinesFromField(report.recommendations));
  }, [report]);

  const originalExplanation = htmlToPlainText(report.explanation || "");
  const originalFlags = plainLinesFromField(report.risk_flags);
  const originalRecs = plainLinesFromField(report.recommendations);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload: any = {};
      const hasRef = refName.trim() && refText.trim();

      if (comment.trim()) payload.comment = comment.trim();
      if (score !== String(report.compliance_score ?? "")) payload.compliance_score = Number(score);
      if (risk !== report.risk_level) payload.risk_level = risk;
      if (explanation !== originalExplanation) payload.explanation = explanation;
      if (flags !== originalFlags) payload.risk_flags = flags;
      if (recs !== originalRecs) payload.recommendations = recs;

      if (hasRef) {
        payload.reference = {
          document_name: refName.trim(),
          reference_text: refText.trim(),
          comment: refComment.trim() || comment.trim(),
        };
      }

      const hasEdits = Object.keys(payload).some((k) => k !== "reference" && k !== "comment");
      if (!hasEdits && !hasRef) {
        setError("Change at least one field or add a reference.");
        return;
      }
      if (hasEdits && !comment.trim()) {
        setError("Validation comment is required when editing compliance fields.");
        return;
      }

      await reportsApi.applyAmendments(report.report_id, payload);
      setComment("");
      setRefName("");
      setRefText("");
      setRefComment("");
      onSaved();
    } catch (err: any) {
      setError(err?.response?.data?.error || err.message || "Failed to save amendment");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="glass rounded-[2rem] p-6 border-white/10 space-y-6">
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-white/40">
          Manual Evaluation & Amendments
        </h3>
        <p className="mt-2 text-sm text-white/50">
          Override AI-generated compliance fields, cite regulatory sources, and record validated changes.
          All edits are logged and visible to the company.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="space-y-1.5">
          <span className="text-[10px] uppercase tracking-wider text-white/40">Compliance score</span>
          <input
            type="number"
            min={0}
            max={100}
            value={score}
            onChange={(e) => setScore(e.target.value)}
            disabled={disabled || saving}
            className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="space-y-1.5">
          <span className="text-[10px] uppercase tracking-wider text-white/40">Risk level</span>
          <select
            value={risk}
            onChange={(e) => setRisk(e.target.value)}
            disabled={disabled || saving}
            className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white"
          >
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
          </select>
        </label>
      </div>

      <label className="block space-y-1.5">
        <span className="text-[10px] uppercase tracking-wider text-white/40">Determination summary</span>
        <textarea
          value={explanation}
          onChange={(e) => setExplanation(e.target.value)}
          disabled={disabled || saving}
          rows={20}
          className={`${textareaClass} min-h-[480px]`}
        />
      </label>

      <div className="grid gap-4 md:grid-cols-2 md:items-stretch">
        <label className="flex flex-col space-y-1.5">
          <span className="text-[10px] uppercase tracking-wider text-white/40">Risk flags (one per line)</span>
          <textarea
            value={flags}
            onChange={(e) => setFlags(e.target.value)}
            disabled={disabled || saving}
            rows={12}
            className={`${textareaClass} min-h-[260px] flex-1`}
          />
        </label>
        <label className="flex flex-col space-y-1.5">
          <span className="text-[10px] uppercase tracking-wider text-white/40">Required actions (one per line)</span>
          <textarea
            value={recs}
            onChange={(e) => setRecs(e.target.value)}
            disabled={disabled || saving}
            rows={12}
            className={`${textareaClass} min-h-[260px] flex-1`}
          />
        </label>
      </div>

      <div className="rounded-xl border border-accent/20 bg-accent/5 p-4 space-y-3">
        <p className="text-xs font-semibold text-accent flex items-center gap-1.5">
          <Plus className="w-3.5 h-3.5" /> Add regulatory reference
        </p>
        <label className="block space-y-1.5">
          <span className="text-[10px] uppercase tracking-wider text-white/40 flex items-center gap-1">
            <FileText className="w-3 h-3 text-accent/70" /> Regulatory document
          </span>
          <RegulatoryDocumentPicker
            catalog={catalog}
            value={refName}
            onChange={setRefName}
            disabled={disabled || saving}
            loading={docsLoading}
          />
        </label>
        <textarea
          placeholder="Quoted regulatory text supporting your change..."
          value={refText}
          onChange={(e) => setRefText(e.target.value)}
          disabled={disabled || saving}
          rows={5}
          className={`${textareaClass} min-h-[140px]`}
        />
        <input
          placeholder="Reference note (optional)"
          value={refComment}
          onChange={(e) => setRefComment(e.target.value)}
          disabled={disabled || saving}
          className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white"
        />
      </div>

      <label className="block space-y-1.5">
        <span className="text-[10px] uppercase tracking-wider text-white/40">
          Validation comment (required for field edits)
        </span>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          disabled={disabled || saving}
          rows={4}
          placeholder="Explain why you are changing the compliance determination..."
          className={`${textareaClass} min-h-[100px]`}
        />
      </label>

      {error && <p className="text-sm text-rose-400">{error}</p>}

      <button
        type="button"
        onClick={handleSave}
        disabled={disabled || saving}
        className="inline-flex items-center gap-2 rounded-2xl bg-accent px-5 py-2.5 text-sm font-bold text-ink hover:bg-white transition disabled:opacity-50"
      >
        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        Save amendments & log changes
      </button>
    </div>
  );
}
