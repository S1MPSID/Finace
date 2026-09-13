const capabilities = [
  {
    title: "Live Regulatory Tracking",
    description: "Monitor RBI, FATF, SEBI, and policy notices in one place with visible version history.",
  },
  {
    title: "Workflow Risk Detection",
    description: "Submit product flows and surface likely compliance issues before launch or audit review.",
  },
  {
    title: "Explainable Compliance",
    description: "Every risk includes the legal clause, plain-language explanation, and why it matters.",
  },
  {
    title: "Legal Document Studio",
    description: "Generate first-pass Privacy Policy and Terms of Service drafts from product details.",
  },
  {
    title: "Immutable Audit Trail",
    description: "Record compliance checks, timestamps, and blockchain proofs for future verification.",
  },
  {
    title: "Regulator Review Layer",
    description: "Give auditors a separate review surface to validate AI findings and leave comments.",
  },
];

const workflowSteps = [
  "Ingest and update regulatory sources",
  "Embed and organize the knowledge base",
  "Analyze startup workflows with RAG",
  "Explain risks with clause references",
  "Store proofs and export compliance reports",
];
export function ProblemSection() {
  return (
    <section className="bg-mist py-20 text-slate-900">
      <div className="shell grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
        <div className="space-y-5">
          <span className="section-label border-slate-200 bg-white text-slate-600">
            Why It Matters
          </span>
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Startups need compliance clarity, not legal bottlenecks.
          </h2>
          <p className="max-w-xl text-base leading-8 text-slate-600">
            The interface should present complex regulation as something traceable,
            understandable, and actionable for product teams, founders, and auditors.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            "Manual legal review slows launches and creates inconsistency.",
            "Regulatory updates are hard to track across multiple authorities.",
            "Most tools show risk flags without transparent legal reasoning.",
            "Audit histories are often fragmented and difficult to verify.",
          ].map((problem) => (
            <div key={problem} className="rounded-[1.6rem] border border-slate-200 bg-white p-6 shadow-sm">
              <p className="text-sm leading-7 text-slate-700">{problem}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function CapabilitiesSection() {
  return (
    <section id="capabilities" className="py-20">
      <div className="shell">
        <div className="mb-10 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <span className="section-label">Platform Capabilities</span>
            <h2 className="mt-5 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              Built as one continuous compliance surface.
            </h2>
          </div>
          <p className="max-w-xl text-sm leading-7 text-white/60">
            Each module is planned as part of the same visual system so the product feels cohesive
            from first visit through audit review.
          </p>
        </div>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {capabilities.map((item) => (
            <div key={item.title} className="glass rounded-[1.8rem] p-6">
              <p className="text-sm text-accent">Module</p>
              <h3 className="mt-4 text-2xl font-semibold text-white">{item.title}</h3>
              <p className="mt-4 text-sm leading-7 text-white/65">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function WorkflowSection() {
  return (
    <section className="py-20">
      <div className="shell grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-[#0d1413] to-[#11231f] p-8 shadow-glow">
          <span className="section-label">System Flow</span>
          <h2 className="mt-5 text-3xl font-semibold tracking-tight text-white">
            The UI should make the compliance journey feel visible.
          </h2>
          <p className="mt-5 text-sm leading-7 text-white/65">
            Users should understand where the answer came from, what is risky, and what proof was
            recorded, all without digging through technical logs.
          </p>
        </div>
        <div className="grid gap-4">
          {workflowSteps.map((step, index) => (
            <div
              key={step}
              className="glass flex items-center gap-4 rounded-[1.6rem] px-5 py-5"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent text-sm font-semibold text-ink">
                0{index + 1}
              </div>
              <p className="text-base text-white/85">{step}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function UseCaseSection() {
  const cards = [
    "Fintech onboarding reviews",
    "Crypto product launch checks",
    "Founder-friendly legal summaries",
    "Auditor-facing immutable evidence",
  ];

  return (
    <section className="bg-mist py-20 text-slate-900">
      <div className="shell">
        <span className="section-label border-slate-200 bg-white text-slate-600">Use Cases</span>
        <div className="mt-6 grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Designed for teams building in regulated markets.
            </h2>
            <p className="mt-5 max-w-xl text-base leading-8 text-slate-600">
              The UI should look trustworthy enough for compliance teams while still being simple
              enough for product and operations teams to use daily.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {cards.map((card) => (
              <div key={card} className="rounded-[1.6rem] border border-slate-200 bg-white p-6">
                <p className="text-sm font-medium uppercase tracking-[0.18em] text-slate-400">
                  Scenario
                </p>
                <h3 className="mt-4 text-2xl font-semibold text-slate-900">{card}</h3>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
