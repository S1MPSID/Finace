import type { ReactNode } from "react";
import {
  Area,
  Bar,
  BarChart,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { Activity, BadgeCheck, BrainCircuit, Sparkles } from "lucide-react";
import type { TrustAnalytics } from "@/lib/trust/types";
import { ACCENT_HEX } from "@/lib/theme/colors";
import { ChartTip } from "./ChartTip";

export function TrustChartGrid({ stats }: { stats: TrustAnalytics }) {
  return (
    <>
      <div className="grid gap-5 lg:grid-cols-2">
        <ChartCard icon={Activity} title="Score trajectory" subtitle="Compliance score vs surrogate across turns">
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
            <Line type="monotone" dataKey="surrogate" name="Surrogate" stroke="#94a3b8" strokeDasharray="4 4" strokeWidth={1.5} dot={false} />
          </ComposedChart>
        </ChartCard>

        <ChartCard icon={BadgeCheck} title="Risk mix" subtitle="How often the session landed HIGH / MEDIUM / LOW">
          <PieChart>
            <Pie data={stats.riskPie} dataKey="value" nameKey="name" innerRadius={48} outerRadius={78} paddingAngle={3}>
              {stats.riskPie.map((row) => (
                <Cell key={row.name} fill={row.fill} />
              ))}
            </Pie>
            <Tooltip content={<ChartTip />} />
            <Legend verticalAlign="bottom" formatter={(value) => <span className="text-[11px] text-white/60">{value}</span>} />
          </PieChart>
        </ChartCard>

        <ChartCard icon={BrainCircuit} title="Latest SHAP drivers" subtitle="What pushed the newest score up or down">
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

        <ChartCard icon={Sparkles} title="Trust factors" subtitle="Composite signals behind the trust index">
          <BarChart data={stats.factorRadar}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: "rgba(255,255,255,0.45)", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTip />} />
            <Bar dataKey="score" name="Factor" fill={ACCENT_HEX} radius={[6, 6, 0, 0]} barSize={28} />
          </BarChart>
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
        </section>
      </div>
    </>
  );
}

function ChartCard({
  icon: Icon,
  title,
  subtitle,
  children,
}: {
  icon: any;
  title: string;
  subtitle: string;
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
      </div>
    </section>
  );
}

function EmptyChart({ label }: { label: string }) {
  return <p className="flex h-full items-center justify-center text-sm text-white/40">{label}</p>;
}
