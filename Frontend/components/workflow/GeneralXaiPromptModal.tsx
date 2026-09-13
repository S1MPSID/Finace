"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

type Props = {
  open: boolean;
  onEnable: (shap: boolean, semanticMl: boolean) => void;
  onDecline: () => void;
};

export function GeneralXaiPromptModal({ open, onEnable, onDecline }: Props) {
  const [ready, setReady] = useState(false);
  const [shap, setShap] = useState(true);
  const [semantic, setSemantic] = useState(true);

  useEffect(() => setReady(true), []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDecline();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onDecline]);

  if (!open || !ready) return null;

  return createPortal(
    <div className="fixed inset-0 z-[9998] flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <button type="button" aria-label="Dismiss" className="absolute inset-0 bg-black/90" onClick={onDecline} />
      <div
        className="relative z-10 w-full max-w-md rounded-2xl border border-white/20 bg-[#121a18] p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold text-white">Explainability for this chat?</h2>
        <p className="mt-2 text-sm leading-relaxed text-white/65">
          General Q&amp;A can show <strong className="text-white/85">SHAP driver bars</strong> and{" "}
          <strong className="text-white/85">semantic ML control checks</strong> (trained on your regulation corpus) alongside
          answers. You can turn these on or off anytime via the settings icon next to Send.
        </p>
        <div className="mt-4 space-y-3 rounded-xl border border-white/10 bg-black/25 p-3">
          <label className="flex cursor-pointer items-center justify-between gap-3 text-sm text-white/85">
            Enable SHAP (driver bars)
            <input type="checkbox" checked={shap} onChange={(e) => setShap(e.target.checked)} className="accent-emerald-400" />
          </label>
          <label className="flex cursor-pointer items-center justify-between gap-3 text-sm text-white/85">
            Enable semantic ML checks
            <input
              type="checkbox"
              checked={semantic}
              onChange={(e) => setSemantic(e.target.checked)}
              className="accent-emerald-400"
            />
          </label>
        </div>
        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onDecline}
            className="rounded-full border border-white/15 px-4 py-2.5 text-sm text-white/75 hover:bg-white/5"
          >
            Not now
          </button>
          <button
            type="button"
            onClick={() => onEnable(shap, semantic)}
            className="rounded-full bg-accent px-4 py-2.5 text-sm font-semibold text-ink hover:bg-accent/90"
          >
            Continue
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
