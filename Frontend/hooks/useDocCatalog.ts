"use client";

import { useEffect, useState } from "react";
import { docsApi } from "@/services/api";
import { DocEntry, flattenDocsTree } from "@/lib/docs/docCatalog";

export function useDocCatalog() {
  const [catalog, setCatalog] = useState<DocEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res: any = await docsApi.getTree();
        if (!cancelled) setCatalog(flattenDocsTree(res?.data || []));
      } catch {
        if (!cancelled) setCatalog([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { catalog, loading };
}
