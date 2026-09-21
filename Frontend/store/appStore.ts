import { create } from "zustand";
import { reportsApi } from "@/services/api";

interface User {
  id: string;
  name: string;
  role: "admin" | "evaluator" | "user";
  company_name?: string;
  email?: string;
}

interface AppState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User, token?: string) => void;
  logout: () => void;
  
  // Active workflow state
  activeReportId: string | null;
  setActiveReportId: (id: string | null) => void;

  // Cached API Data
  reports: any[];
  auditLogs: any[];
  isLoading: boolean;
  error: string | null;
  fetchReports: () => Promise<void>;
}

// Helper to safely get from localStorage
const getInitialState = () => {
  if (typeof window === "undefined") return { user: null, isAuthenticated: false };
  
  const token = localStorage.getItem("token");
  const storedUser = localStorage.getItem("user");
  
  if (token && storedUser) {
    try {
      return { user: JSON.parse(storedUser), isAuthenticated: true };
    } catch {
      return { user: null, isAuthenticated: false };
    }
  }
  return { user: null, isAuthenticated: false };
};

const initialState = getInitialState();

export const useAppStore = create<AppState>((set) => ({
  user: initialState.user,
  isAuthenticated: initialState.isAuthenticated,
  
  login: (user, token) => {
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
    }
    set({ user, isAuthenticated: true });
  },
  
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
    set({ user: null, isAuthenticated: false, reports: [], auditLogs: [] });
  },
  
  activeReportId: null,
  setActiveReportId: (id) => set({ activeReportId: id }),

  reports: [],
  auditLogs: [],
  isLoading: false,
  error: null,
  
  fetchReports: async () => {
    set({ isLoading: true, error: null });
    try {
      const data: any = await reportsApi.getAll();
      set({ 
        reports: data.reports || [], 
        auditLogs: (data.reports || []).filter((r: any) => r.ipfs_cid || r.tx_hash),
        isLoading: false 
      });
    } catch (err: any) {
      set({ error: err.message || "Failed to fetch reports", isLoading: false });
    }
  }
}));
