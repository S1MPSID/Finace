import { motion } from "framer-motion";
import { WORKFLOW_SUGGESTIONS } from "@/lib/workflow/constants";
import { WorkflowComposer } from "./WorkflowComposer";

interface Props {
  input: string;
  loading: boolean;
  finalizing: boolean;
  onInputChange: (value: string) => void;
  onSend: (text?: string) => void;
  onFinalize: () => void;
}

export function WorkflowEmptyState({
  input,
  loading,
  finalizing,
  onInputChange,
  onSend,
  onFinalize,
}: Props) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 pb-8 pt-16">
      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 text-center text-[28px] font-medium tracking-tight text-white sm:text-[32px]"
      >
        What&apos;s the compliance question?
      </motion.h1>

      <WorkflowComposer
        input={input}
        loading={loading}
        finalizing={finalizing}
        hasMessages={false}
        onInputChange={onInputChange}
        onSend={() => onSend()}
        onFinalize={onFinalize}
      />

      <div className="mt-6 flex max-w-3xl flex-wrap justify-center gap-2 px-4">
        {WORKFLOW_SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSend(s)}
            className="rounded-full border border-white/10 bg-transparent px-3.5 py-2 text-left text-[13px] text-white/55 hover:bg-white/[0.06] hover:text-white/85 transition"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
