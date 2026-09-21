"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { hydrateAuth, loginSuccess } from "@/store/slices/authSlice";
import { evaluatorAuthApi, userAuthApi } from "@/services/api";
import { getAuthToken } from "@/lib/authCookies";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, Lock, User as UserIcon, Mail, BadgeCheck, Building2, Loader2 } from "lucide-react";

type LoginRole = "company" | "evaluator";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<LoginRole>("company");
  const [isRegistering, setIsRegistering] = useState(false);
  const router = useRouter();
  const dispatch = useAppDispatch();
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated);
  const authReady = useAppSelector((s) => s.auth.authReady);
  const authUser = useAppSelector((s) => s.auth.user);

  useEffect(() => {
    if (!authReady) dispatch(hydrateAuth());
  }, [authReady, dispatch]);

  useEffect(() => {
    if (authReady && isAuthenticated) {
      router.replace(authUser?.role === "evaluator" ? "/dashboard/evaluator" : "/dashboard");
    }
  }, [authReady, isAuthenticated, authUser?.role, router]);

  const finishLogin = (user: any, token: string, dest: string) => {
    dispatch(loginSuccess({ user, token }));
    const saved = getAuthToken();
    if (!saved) {
      throw new Error("Could not save session cookie. Allow cookies for localhost and try again.");
    }
    window.location.assign(dest);
  };

  const handleCompanyLogin = async () => {
    const data: any = await userAuthApi.login(email, password);
    if (data.ok && data.token) {
      finishLogin(data.user, data.token, "/dashboard");
      return;
    }
    throw new Error(data.error || "Login failed");
  };

  const handleCompanyRegister = async () => {
    const data: any = await userAuthApi.register(name, email, password);
    if (data.ok && data.token) {
      finishLogin(data.user, data.token, "/dashboard");
      return;
    }
    throw new Error(data.error || "Registration failed");
  };

  const handleEvaluatorLogin = async () => {
    const data: any = await evaluatorAuthApi.login(email, password);
    if (data.ok && data.token) {
      finishLogin(
        {
          id: data.evaluator.evaluator_id,
          name: data.evaluator.name,
          role: "evaluator",
          email: data.evaluator.email,
        },
        data.token,
        "/dashboard/evaluator"
      );
      return;
    }
    throw new Error(data.error || "Login failed");
  };

  const handleEvaluatorRegister = async () => {
    const data: any = await evaluatorAuthApi.register(name, email, password);
    if (data.ok && data.token) {
      finishLogin(
        {
          id: data.evaluator.evaluator_id,
          name: data.evaluator.name,
          role: "evaluator",
          email: data.evaluator.email,
        },
        data.token,
        "/dashboard/evaluator"
      );
      return;
    }
    throw new Error(data.error || "Registration failed");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    setLoading(true);
    setError(null);

    try {
      if (role === "company") {
        if (isRegistering) await handleCompanyRegister();
        else await handleCompanyLogin();
      } else if (isRegistering) {
        await handleEvaluatorRegister();
      } else {
        await handleEvaluatorLogin();
      }
      // Keep loading true through navigation
    } catch (err: any) {
      setError(err.response?.data?.message || err.response?.data?.error || err.message || "Login failed");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#071010] flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-accent/20 rounded-full blur-[120px] opacity-50" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[120px] opacity-50" />

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="glass rounded-[2rem] p-8 border border-white/10 relative z-10">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mb-4">
              <ShieldCheck className="w-8 h-8 text-accent" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Finace Platform</h1>
            <p className="text-white/50 text-sm mt-2">Autonomous Compliance Engine</p>
          </div>

          <div className="flex rounded-2xl border border-white/10 overflow-hidden mb-6">
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setRole("company");
                setIsRegistering(false);
                setError(null);
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-all disabled:opacity-50 ${
                role === "company"
                  ? "bg-accent/15 text-accent border-r border-white/10"
                  : "text-white/40 hover:text-white/60 border-r border-white/10"
              }`}
            >
              <Building2 className="w-4 h-4" /> Company
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setRole("evaluator");
                setIsRegistering(false);
                setError(null);
              }}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-all disabled:opacity-50 ${
                role === "evaluator" ? "bg-accent/15 text-accent" : "text-white/40 hover:text-white/60"
              }`}
            >
              <BadgeCheck className="w-4 h-4" /> Evaluator
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <AnimatePresence mode="wait">
              {isRegistering && (
                <motion.div
                  key="name-field"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-1.5"
                >
                  <label className="text-xs font-medium text-white/60 uppercase tracking-wider pl-1">
                    {role === "company" ? "Company Name" : "Full Name"}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                      <UserIcon className="h-5 w-5 text-white/30" />
                    </div>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      disabled={loading}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all disabled:opacity-60"
                      placeholder={role === "company" ? "Acme Corp" : "John Doe"}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/60 uppercase tracking-wider pl-1">
                {role === "company" ? "Username" : "Email"}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-white/30" />
                </div>
                <input
                  type="text"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all disabled:opacity-60"
                  placeholder={role === "company" ? "admin_acme" : "evaluator@finace.io"}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/60 uppercase tracking-wider pl-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-white/30" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-accent/50 transition-all disabled:opacity-60"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <p className="text-sm text-rose-400 bg-rose-400/10 px-4 py-2 rounded-xl border border-rose-500/20">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              aria-busy={loading}
              className={`relative w-full mt-6 font-semibold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2.5 overflow-hidden ${
                loading
                  ? "bg-accent/80 text-ink cursor-wait"
                  : "bg-accent hover:bg-accent/90 text-ink"
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>{isRegistering ? "Creating account…" : "Signing in…"}</span>
                </>
              ) : (
                <span>{isRegistering ? "Create Account" : "Sign In"}</span>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError(null);
              }}
              className="text-sm text-accent/70 hover:text-accent transition disabled:opacity-40"
            >
              {isRegistering
                ? "Already have an account? Sign in"
                : `New ${role === "company" ? "company" : "evaluator"}? Create account`}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
