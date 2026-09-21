import type { ReactNode } from "react";
import {
  Area,
  Bar,
  BarChart,
  Cell,
  ComposedChart,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { Activity, BrainCircuit } from "lucide-react";
import type { TrustAnalytics } from "@/lib/trust/types";
import { ACCENT_HEX } from "@/lib/theme/colors";
import { ChartTip } from "./ChartTip";

export function TrustChartGrid({ stats }: { stats: TrustAnalytics }) {
  return (
    <>
      <div className="grid gap-5 lg:grid-cols-2">
        <ChartCard icon={Activity} title="Overall compliance score" subtitle="Score movement across analyzed turns" inference="A higher score means more controls were detected by FINACE; it is not a legal approval or probability of compliance.">
          <ComposedChart data={stats.scoreSeries}>
            <defs>
              <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={ACCENT_HEX} stopOpacity={0.35} />
                <stop offset="100%" stopColor={ACCENT_HEX} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="turn" tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTip />} />
            <Area type="monotone" dataKey="score" name="Score" stroke={ACCENT_HEX} fill="url(#scoreFill)" strokeWidth={2} />
          </ComposedChart>
        </ChartCard>

        <ChartCard icon={BrainCircuit} title="Top ML risk drivers" subtitle="Features with the largest model contribution" inference="Positive bars increase the model's predicted HIGH-risk score; negative bars reduce it. These are model contributions, not legal conclusions.">
          {stats.shapBars.length ? (
            <BarChart data={stats.shapBars} layout="vertical" margin={{ left: 4, right: 12 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="name" width={100} tick={{ fill: "rgba(255,255,255,0.55)", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTip />} />
              <Bar dataKey="value" name="SHAP" radius={[0, 4, 4, 0]} barSize={12}>
                {stats.shapBars.map((row) => (
                  <Cell key={row.name} fill={row.fill} />
                ))}
              </Bar>
            </BarChart>
          ) : (
            <EmptyChart label="No SHAP features yet" />
          )}
        </ChartCard>

      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <section className="glass rounded-2xl p-4">
          <h3 className="mb-1 text-sm font-medium text-white">Control coverage</h3>
          <p className="mb-3 text-[11px] text-white/40">Which compliance controls the latest turn detected</p>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.controlBars}>
                <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 1]} ticks={[0, 1]} tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTip />} />
                <Bar dataKey="value" name="Present" radius={[6, 6, 0, 0]} barSize={26}>
                  {stats.controlBars.map((row) => (
                    <Cell key={row.name} fill={row.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-[11px] leading-5 text-white/45"><span className="text-accent/80">Inference:</span> This shows the proportion of detected protective controls. A missing control is a workflow gap; it is not automatically a proven regulatory violation.</p>
        </section>

        <section className="glass rounded-2xl p-4">
          <h3 className="mb-1 text-sm font-medium text-white">Retrieval strength</h3>
          <p className="mb-3 text-[11px] text-white/40">How strongly regulations backed the latest decision</p>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.retrievalBars}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTip />} />
                <Line type="monotone" dataKey="value" name="Strength %" stroke={ACCENT_HEX} strokeWidth={2} dot={{ r: 4, fill: ACCENT_HEX }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-[11px] leading-5 text-white/45"><span className="text-accent/80">Inference:</span> Strong retrieval means the indexed corpus matched the query semantically. It does not prove that the retrieved clause legally applies to the entity.</p>
        </section>
      </div>
    </>
  );
}

function ChartCard({
  icon: Icon,
  title,
  subtitle,
  inference,
  children,
}: {
  icon: any;
  title: string;
  subtitle: string;
  inference?: string;
  children: ReactNode;
}) {
  return (
    <section className="glass rounded-2xl p-4">
      <div className="relative z-[1]">
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4 text-accent" />
        <div>
          <h3 className="text-sm font-medium text-white">{title}</h3>
          <p className="text-[11px] text-white/40">{subtitle}</p>
        </div>
      </div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer>
      </div>
      {inference && <p className="mt-3 text-[11px] leading-5 text-white/45"><span className="text-accent/80">Inference:</span> {inference}</p>}
      </div>
    </section>
  );
}

function EmptyChart({ label }: { label: string }) {
  return <p className="flex h-full items-center justify-center text-sm text-white/40">{label}</p>;
}
