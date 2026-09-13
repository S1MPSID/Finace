"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { AuthGuard } from "@/components/dashboard/auth-guard";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthGuard>
      <DashboardShell>{children}</DashboardShell>
    </AuthGuard>
  );
}

function DashboardShell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const pathname = usePathname();
  const isStudio = pathname?.startsWith("/dashboard/workflow");

  return (
    <main className="relative flex h-screen overflow-hidden bg-[#050908]">
      <div className="pointer-events-none absolute inset-0 dashboard-grid" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_100%_55%_at_50%_-8%,rgba(34,160,96,0.22),transparent_58%)]" />
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-32 -left-20 h-[28rem] w-[28rem] rounded-full bg-accent/12 blur-[120px]" />
        <div className="absolute top-[38%] -right-24 h-[32rem] w-[32rem] rounded-full bg-emerald-500/8 blur-[130px]" />
        <div className="absolute -bottom-24 left-[28%] h-72 w-72 rounded-full bg-teal-400/6 blur-[100px]" />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_32%,rgba(0,0,0,0.48)_100%)]" />
      <div className="dashboard-noise pointer-events-none absolute inset-0" />
      <div className="relative z-10 flex h-full w-full min-w-0">
        <DashboardSidebar open={sidebarOpen} onToggle={() => setSidebarOpen((v) => !v)} />
        <section
          className={`min-w-0 flex-1 ${isStudio ? "overflow-hidden" : "overflow-y-auto p-5 sm:p-7 lg:p-8"}`}
        >
          {children}
        </section>
      </div>
    </main>
  );
}
