"use client";

export function EvidenceScopeNotice({ scope }: { scope?: any }) {
  if (!scope) return null;
  const warnings: string[] = scope.warnings || [];
  const unresolved: string[] = scope.unresolved_domains || [];
  if (!warnings.length && !unresolved.length) return null;

  return (
    <div className="rounded-[1.4rem] border border-amber-300/20 bg-amber-400/10 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-amber-200">
        Evidence applicability warning
      </p>
      <p className="mt-2 text-sm leading-6 text-amber-50/80">
        The workflow contains regulated domains for which the indexed corpus did not establish a directly applicable clause. These findings are potential exposure assessments, not definitive legal violations.
      </p>
      {warnings.slice(0, 3).map((warning) => (
        <p key={warning} className="mt-2 text-xs leading-5 text-amber-100/70">{warning}</p>
      ))}
    </div>
  );
}
