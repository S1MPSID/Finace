import { ACCENT_HEX } from "@/lib/theme/colors";

export function ChartTip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-white/15 bg-[#121a18] px-3 py-2 shadow-lg">
      {label != null && <p className="text-[11px] text-white/45 mb-1">{label}</p>}
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-[12px] font-medium text-white/90">
          <span style={{ color: p.color || ACCENT_HEX }}>{p.name || "value"}</span>
          {": "}
          {typeof p.value === "number"
            ? Number.isInteger(p.value)
              ? p.value
              : p.value.toFixed(2)
            : p.value}
        </p>
      ))}
    </div>
  );
}
