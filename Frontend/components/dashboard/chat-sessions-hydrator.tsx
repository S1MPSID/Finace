"use client";

import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { fetchChatSessions, markChatSessionsLoaded } from "@/store/slices/chatSessionsSlice";

/** Loads chat recents once per login. No polling. */
export function ChatSessionsHydrator() {
  const dispatch = useAppDispatch();
  const authReady = useAppSelector((s) => s.auth.authReady);
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  const userRole = useAppSelector((s) => s.auth.user?.role);
  const loaded = useAppSelector((s) => s.chatSessions.loaded);

  useEffect(() => {
    if (!authReady || !isAuthenticated || loaded) return;
    if (!userRole) return;
    if (userRole === "evaluator") {
      dispatch(markChatSessionsLoaded());
      return;
    }
    dispatch(fetchChatSessions());
  }, [authReady, isAuthenticated, userRole, loaded, dispatch]);

  return null;
}
