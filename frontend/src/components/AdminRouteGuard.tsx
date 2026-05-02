import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";
import { SkeletonBlock } from "./shared/UI";
import { useAdminCapabilities } from "../hooks/queries";


export function AdminRouteGuard() {
  const { session, loading } = useAuth();
  const capabilities = useAdminCapabilities(Boolean(session));

  if (loading || (session && capabilities.isLoading)) {
    return <SkeletonBlock label="載入管理權限中..." />;
  }
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  if (!capabilities.data?.is_admin) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
