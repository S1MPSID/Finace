"use client";

import { Suspense } from "react";
import WorkflowChatPage from "./WorkflowChatInner";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="flex h-full items-center justify-center bg-[#212121] text-white/40 text-sm">
          Loading studio…
        </div>
      }
    >
      <WorkflowChatPage />
    </Suspense>
  );
}
