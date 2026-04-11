import { Navigate, Outlet, useLocation } from "react-router-dom";
import { hasStoredAppSecret } from "../lib/auth";

export function RequireAuth() {
  const location = useLocation();

  if (!hasStoredAppSecret()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
