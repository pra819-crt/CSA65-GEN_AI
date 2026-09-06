"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { UserPlus, Loader2, ShieldCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isAuthenticated, isLoading, error, clearError } = useAuth();
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError(null);

    if (password !== confirmPassword) {
      setLocalError("Passwords do not match.");
      return;
    }
    if (password.length < 6) {
      setLocalError("Password must be at least 6 characters.");
      return;
    }
    if (!/^[a-zA-Z0-9_]{3,32}$/.test(username)) {
      setLocalError(
        "Username must be 3-32 characters: letters, numbers, underscores only."
      );
      return;
    }

    const success = await register(username, password, fullName || undefined);
    if (success) {
      router.replace("/");
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-500">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-2xl p-6">
        <div className="flex items-center gap-2 mb-1">
          <span className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 text-white shrink-0">
            <ShieldCheck size={18} />
          </span>
          <h1 className="text-lg font-bold text-slate-900">GenTwin</h1>
        </div>
        <p className="text-xs text-slate-500 mb-6">
          Create your account to start simulating supply chain disruptions.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="text-xs text-slate-500 mb-1 block" htmlFor="fullName">
              Full Name <span className="text-slate-400">(optional)</span>
            </label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="auth-input focus:ring-emerald-300 focus:border-emerald-400"
              placeholder="Praveen Kumar"
            />
          </div>

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
              className="auth-input focus:ring-emerald-300 focus:border-emerald-400"
              placeholder="3-32 characters, letters/numbers/_"
            />
          </div>

          <div>
            <label className="text-xs text-slate-500 mb-1 block" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="auth-input focus:ring-emerald-300 focus:border-emerald-400"
              placeholder="At least 6 characters"
            />
          </div>

          <div>
            <label
              className="text-xs text-slate-500 mb-1 block"
              htmlFor="confirmPassword"
            >
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="auth-input focus:ring-emerald-300 focus:border-emerald-400"
              placeholder="Re-enter your password"
            />
          </div>

          {(localError || error) && (
            <p className="text-xs text-status-critical">{localError || error}</p>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-sm disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {isLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <UserPlus size={16} />
            )}
            {isLoading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="text-xs text-slate-500 mt-5 text-center">
          Already have an account?{" "}
          <Link href="/login" className="text-emerald-600 font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
