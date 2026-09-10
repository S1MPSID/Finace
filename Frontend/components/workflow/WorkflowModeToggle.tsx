import type { StudioMode } from "@/lib/workflow/types";

interface Props {
  mode: StudioMode;
  onChange: (mode: StudioMode) => void;
}

export function WorkflowModeToggle({ mode, onChange }: Props) {
  return (
    <div className="absolute left-1/2 top-3 z-10 -translate-x-1/2">
      <div className="inline-flex items-center rounded-full border border-white/10 bg-white/[0.04] backdrop-blur-xl p-0.5 text-xs">
        {(["chat", "analyze"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => onChange(tab)}
            className={`rounded-full px-3 py-1 capitalize transition ${
              mode === tab
                ? "bg-accent/15 font-medium text-accent"
                : "text-white/40 hover:text-white/70"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>
    </div>
  );
}
