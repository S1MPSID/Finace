"use client";

import { useState } from "react";
import type { Route } from "next";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  BookOpen,
  Scale,
  ScrollText,
  LogOut,
  User as UserIcon,
  PanelLeftClose,
  PanelLeft,
  Plus,
  Search,
  Trash2,
  ShieldCheck,
} from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { logout as logoutAction } from "@/store/slices/authSlice";
import { removeChatSession, upsertChatSession } from "@/store/slices/chatSessionsSlice";
import { chatHistoryApi } from "@/services/api";

const items = [
  { href: "/dashboard" as Route, label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/workflow" as Route, label: "Analyze workflow", icon: MessageSquare },
  { href: "/dashboard/regulations" as Route, label: "Regulations", icon: BookOpen },
  { href: "/dashboard/evaluator" as Route, label: "Reports & review", icon: Scale },
  { href: "/dashboard/audit" as Route, label: "Proof ledger", icon: ScrollText },
];

export function DashboardSidebar({
  open,
  onToggle,
}: {
  open: boolean;
  onToggle: () => void;
}) {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);
  const isEvaluator = user?.role === "evaluator";
  const sessions = useAppSelector((s) => s.chatSessions.sessions);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeChatId = searchParams.get("chat");
  const [query, setQuery] = useState("");

  const handleLogout = () => {
    dispatch(logoutAction());
    router.push("/login");
  };

  const handleNewChat = () => {
    router.push("/dashboard/workflow?new=1");
  };

  const handleOpenSession = (id: string) => {
    router.push(`/dashboard/workflow?chat=${id}`);
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    const removed = sessions.find((s) => s.session_id === id);
    dispatch(removeChatSession(id));
    try {
      await chatHistoryApi.remove(id);
      if (pathname.includes("workflow")) {
        const params = new URLSearchParams(window.location.search);
        if (params.get("chat") === id) router.push("/dashboard/workflow?new=1");
      }
    } catch {
      if (removed) dispatch(upsertChatSession(removed));
    }
  };

  const filtered = sessions.filter((s) =>
    !query.trim() ? true : s.title.toLowerCase().includes(query.trim().toLowerCase())
  );

  if (!open) {
    return (
      <aside className="flex w-[56px] shrink-0 flex-col items-center gap-2 border-r border-white/[0.05] bg-[#080f0e]/80 backdrop-blur-xl py-3">
        <button
          type="button"
          onClick={onToggle}
          className="flex h-9 w-9 items-center justify-center rounded-xl text-white/45 hover:bg-accent/10 hover:text-accent transition"
          title="Open sidebar"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={handleNewChat}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-accent/25 bg-accent/10 text-accent hover:bg-accent/20 transition"
          title="New chat"
        >
          <Plus className="h-4 w-4" />
        </button>
        <div className="mt-auto pb-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-accent/20 bg-accent/10 text-accent">
            <UserIcon className="h-3.5 w-3.5" />
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex w-[268px] shrink-0 flex-col border-r border-white/[0.05] bg-[#080f0e]/75 backdrop-blur-xl">
      <div className="flex items-center justify-between gap-2 px-3 pt-4 pb-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-accent/25 bg-accent/10">
            <ShieldCheck className="h-4 w-4 text-accent" />
          </div>
          <div className="min-w-0">
            <p className="text-[15px] font-semibold tracking-tight text-white">Finace</p>
            <p className="text-[10px] uppercase tracking-[0.16em] text-white/35">Console</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="flex h-8 w-8 items-center justify-center rounded-xl text-white/35 hover:bg-white/5 hover:text-white transition"
          title="Close sidebar"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      {!isEvaluator && (
        <div className="px-3 pb-3">
          <button
            type="button"
            onClick={handleNewChat}
            className="flex w-full items-center gap-2 rounded-2xl border border-accent/30 bg-accent/10 px-3 py-2.5 text-sm font-medium text-accent hover:bg-accent/15 transition"
          >
            <Plus className="h-4 w-4" />
            New chat
          </button>
        </div>
      )}

      <nav className="px-2 space-y-0.5">
        {items
          .filter(
            (item) =>
              !isEvaluator ||
              item.href === "/dashboard/evaluator" ||
              item.href === "/dashboard/audit"
          )
          .map((item) => {
          const active =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13px] transition ${
                active
                  ? "bg-accent/12 text-accent border border-accent/20"
                  : "text-white/55 border border-transparent hover:bg-white/[0.04] hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0 opacity-80" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {!isEvaluator && (
      <div className="mt-4 flex min-h-0 flex-1 flex-col border-t border-white/[0.05] pt-3">
        <p className="px-4 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">
          Recents
        </p>
        <div className="px-3 pb-2">
          <div className="flex items-center gap-2 rounded-xl panel-inset px-2.5 py-1.5">
            <Search className="h-3.5 w-3.5 text-accent/50" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search chats"
              className="w-full bg-transparent text-xs text-white/70 placeholder:text-white/25 focus:outline-none"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-0.5" style={{ scrollbarWidth: "thin" }}>
          {filtered.length === 0 && (
            <p className="px-2 py-3 text-xs text-white/30">No saved chats yet</p>
          )}
          {filtered.map((s) => {
            const activeChat =
              pathname.startsWith("/dashboard/workflow") && activeChatId === s.session_id;
            return (
              <button
                key={s.session_id}
                type="button"
                onClick={() => handleOpenSession(s.session_id)}
                className={`group relative flex w-full items-center rounded-xl px-2.5 py-2 text-left transition ${
                  activeChat ? "bg-accent/10 text-white" : "hover:bg-white/[0.04]"
                }`}
              >
                <span className="truncate pr-6 text-[13px] text-white/65 group-hover:text-white/90">
                  {s.title}
                </span>
                <span
                  role="button"
                  tabIndex={0}
                  onClick={(e) => handleDelete(s.session_id, e)}
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 rounded-lg text-white/30 hover:text-rose-400 hover:bg-rose-500/10"
                >
                  <Trash2 className="h-3 w-3" />
                </span>
              </button>
            );
          })}
        </div>
      </div>
      )}

      {user && (
        <div className="border-t border-white/[0.05] p-2">
          <div className="panel-inset flex items-center gap-2.5 px-2.5 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-accent/20 bg-accent/10 text-accent">
              <UserIcon className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-white/90">{user.name}</p>
              <p className="truncate text-[10px] uppercase tracking-wider text-white/35">{user.role}</p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-white/30 hover:text-rose-400 hover:bg-rose-500/10 transition"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}

export function DashboardNavbar(props: { open?: boolean; onToggle?: () => void }) {
  return (
    <DashboardSidebar open={props.open ?? true} onToggle={props.onToggle ?? (() => {})} />
  );
}
