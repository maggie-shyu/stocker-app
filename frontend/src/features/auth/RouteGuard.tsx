import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./AuthContext";

export function RouteGuard() {
  const { session, loading } = useAuth();
  if (loading) {
    return null;
  }
  return session ? <Outlet /> : <Navigate to="/login" replace />;
}
