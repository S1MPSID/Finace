"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { hydrateAuth } from "@/store/slices/authSlice";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useAppDispatch();
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  const authReady = useAppSelector((s) => s.auth.authReady);

  useEffect(() => {
    if (!authReady) dispatch(hydrateAuth());
  }, [authReady, dispatch]);

  useEffect(() => {
    if (!authReady) return;
    if (!isAuthenticated && pathname !== "/login") {
      router.replace("/login");
    }
  }, [authReady, isAuthenticated, pathname, router]);

  if (!authReady) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#071010]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
          <p className="text-xs text-white/40">Restoring session…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated && pathname !== "/login") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#071010]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
      </div>
    );
  }

  return <>{children}</>;
}
