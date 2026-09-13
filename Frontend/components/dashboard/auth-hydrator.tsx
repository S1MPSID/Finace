"use client";

import { useEffect } from "react";
import { useAppDispatch } from "@/store/hooks";
import { hydrateAuth } from "@/store/slices/authSlice";

/** On every page load: read cookie token → GET /auth/me → Redux auth state. */
export function AuthHydrator() {
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(hydrateAuth());
  }, [dispatch]);

  return null;
}
