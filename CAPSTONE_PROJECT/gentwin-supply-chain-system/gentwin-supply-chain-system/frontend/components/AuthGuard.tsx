"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500">
        <div className="flex items-center gap-2 text-sm text-white bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
          <Loader2 size={16} className="animate-spin" />
          Redirecting to sign in...
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
