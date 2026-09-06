"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { LogIn, Loader2, ShieldCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading, error, clearError } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    const success = await login(username, password);
    if (success) {
      router.replace("/");
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-2xl p-6">
        <div className="flex items-center gap-2 mb-1">
          <span className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shrink-0">
            <ShieldCheck size={18} />
          </span>
          <h1 className="text-lg font-bold text-slate-900">GenTwin</h1>
        </div>
        <p className="text-xs text-slate-500 mb-6">
          Sign in to access the Supply Chain Resilience dashboard.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="text-xs text-slate-500 mb-1 block" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="auth-input"
              placeholder="e.g. praveen"
            />
          </div>

          <div>
            <label className="text-xs text-slate-500 mb-1 block" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="auth-input"
              placeholder="••••••••"
            />
          </div>

          {error && <p className="text-xs text-status-critical">{error}</p>}

          <button type="submit" disabled={isLoading} className="auth-button mt-2">
            {isLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <LogIn size={16} />
            )}
            {isLoading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="text-xs text-slate-500 mt-5 text-center">
          New here?{" "}
          <Link href="/register" className="text-indigo-600 font-medium hover:underline">
            Create an account
          </Link>
        </p>

        <p className="text-[10px] text-slate-400 mt-4 text-center leading-relaxed">
          For your security, you&apos;ll be asked to sign in again every
          time you open this app.
        </p>
      </div>
    </main>
  );
}
