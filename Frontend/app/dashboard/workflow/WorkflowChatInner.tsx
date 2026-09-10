"use client";

import { AnalyzeTrustDashboard } from "@/components/reports/AnalyzeTrustDashboard";
import { useWorkflowChat } from "@/hooks/useWorkflowChat";
import { WorkflowComposer } from "@/components/workflow/WorkflowComposer";
import { WorkflowEmptyState } from "@/components/workflow/WorkflowEmptyState";
import { WorkflowMessageList } from "@/components/workflow/WorkflowMessageList";
import { WorkflowModeToggle } from "@/components/workflow/WorkflowModeToggle";

export default function WorkflowChatPage() {
  const chat = useWorkflowChat();

  const composer = (
    <WorkflowComposer
      input={chat.input}
      loading={chat.loading}
      finalizing={chat.finalizing}
      hasMessages={chat.messages.length > 0}
      onInputChange={chat.setInput}
      onSend={() => chat.handleSendMessage()}
      onFinalize={chat.handleFinalizeReport}
    />
  );

  return (
    <div className="relative flex h-full min-h-0 flex-col bg-transparent">
      <WorkflowModeToggle mode={chat.studioMode} onChange={chat.setStudioMode} />

      {chat.studioMode === "analyze" ? (
        <AnalyzeTrustDashboard messages={chat.messages} />
      ) : chat.empty ? (
        <WorkflowEmptyState
          input={chat.input}
          loading={chat.loading}
          finalizing={chat.finalizing}
          onInputChange={chat.setInput}
          onSend={chat.handleSendMessage}
          onFinalize={chat.handleFinalizeReport}
        />
      ) : (
        <>
          <WorkflowMessageList
            messages={chat.messages}
            loading={chat.loading}
            scrollRef={chat.scrollRef}
          />
          <div className="shrink-0 pb-4 pt-2">{composer}</div>
        </>
      )}
    </div>
  );
}
