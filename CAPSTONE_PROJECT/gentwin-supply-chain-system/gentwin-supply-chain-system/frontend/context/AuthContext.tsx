"use client";

import {
  createContext,
  useCallback,
  useContext,
  useState,
  ReactNode,
} from "react";
import { loginUser, registerUser, setAuthToken } from "@/lib/api";
import { AuthUser } from "@/lib/types";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  register: (
    username: string,
    password: string,
    fullName?: string
  ) => Promise<boolean>;
  logout: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Session state is held ONLY in React memory (useState), never written to
 * localStorage, sessionStorage, or cookies. This is a deliberate design
 * choice: every time the app is reopened (new tab, refresh, browser
 * restart) the user starts unauthenticated and must sign in again with
 * their username and password.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const token = await loginUser(username, password);
      setAuthToken(token.access_token);
      setUser(token.user);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(
    async (username: string, password: string, fullName?: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const token = await registerUser(username, password, fullName);
        setAuthToken(token.access_token);
        setUser(token.user);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Registration failed.");
        return false;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback(() => {
    setAuthToken(null);
    setUser(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        error,
        login,
        register,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
