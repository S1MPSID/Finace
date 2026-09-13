"use client";

import { diffFieldValues, fieldLabel, type DiffLine } from "@/lib/text/lineDiff";

function DiffBlock({ lines }: { lines: DiffLine[] }) {
  if (!lines.length) return null;

  return (
    <div className="mt-2 overflow-hidden rounded-xl border border-accent/35 bg-black/30 font-mono text-[11px] leading-5">
      {lines.map((row, idx) => {
        const isAdd = row.type === "add";
        const prefix = isAdd ? "+++" : "---";
        const num = isAdd ? row.newNum : row.oldNum;
        return (
          <div
            key={`${row.type}-${idx}-${num}`}
            className={`flex gap-2 px-3 py-0.5 ${
              isAdd ? "bg-emerald-500/10 text-emerald-200" : "bg-rose-500/10 text-rose-200"
            }`}
          >
            <span className="w-8 shrink-0 select-none text-white/25">{num}</span>
            <span className="w-7 shrink-0 font-bold select-none">{prefix}</span>
            <span className="min-w-0 flex-1 whitespace-pre-wrap break-words">{row.line}</span>
          </div>
        );
      })}
    </div>
  );
}

export function FieldChangeDiff({
  field,
  oldValue,
  newValue,
}: {
  field: string;
  oldValue: unknown;
  newValue: unknown;
}) {
  const lines = diffFieldValues(oldValue, newValue);
  if (!lines.length) return null;

  return (
    <div className="mt-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-accent/70">{fieldLabel(field)}</p>
      <DiffBlock lines={lines} />
    </div>
  );
}
