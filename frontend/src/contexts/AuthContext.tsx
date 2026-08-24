import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { authApi } from "../services/api";
import type { InvitePayload, InviteResponse, LoginPayload, RegisterPayload, UserProfile, UserRole } from "../types";

interface AuthContextValue {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  invite: (payload: InvitePayload) => Promise<InviteResponse>;
  switchRole: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Rehydrate from localStorage on mount and sync with server
  useEffect(() => {
    const storedToken = localStorage.getItem("vf_access_token");
    const storedUser = localStorage.getItem("vf_user");
    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        
        // Fetch latest profile in background to sync any DB changes
        authApi.me().then(latestUser => {
          setUser(latestUser);
          localStorage.setItem("vf_user", JSON.stringify(latestUser));
        }).catch(() => {
          // If token is invalid/expired, interceptor handles logout
        });
      } catch {
        localStorage.removeItem("vf_access_token");
        localStorage.removeItem("vf_user");
      }
    }
    setIsLoading(false);
  }, []);

  const _persist = useCallback((accessToken: string, userProfile: UserProfile) => {
    localStorage.setItem("vf_access_token", accessToken);
    localStorage.setItem("vf_user", JSON.stringify(userProfile));
    setToken(accessToken);
    setUser(userProfile);
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const data = await authApi.login(payload);
    _persist(data.access_token, data.user);
  }, [_persist]);

  const register = useCallback(async (payload: RegisterPayload) => {
    const data = await authApi.register(payload);
    _persist(data.access_token, data.user);
  }, [_persist]);

  const logout = useCallback(() => {
    localStorage.removeItem("vf_access_token");
    localStorage.removeItem("vf_user");
    setToken(null);
    setUser(null);
  }, []);

  const invite = useCallback(async (payload: InvitePayload) => {
    return await authApi.invite(payload);
  }, []);

  const switchRole = useCallback((newRole: UserRole) => {
    setUser((prev) => {
      if (!prev) return null;
      const updated = { ...prev, role: newRole };
      localStorage.setItem("vf_user", JSON.stringify(updated));
      return updated;
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user && !!token,
        login,
        register,
        logout,
        invite,
        switchRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
