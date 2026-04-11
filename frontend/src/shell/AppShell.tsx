import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { clearStoredAppSecret } from "../lib/auth";

export function AppShell() {
  const navigate = useNavigate();

  function handleLogout() {
    clearStoredAppSecret();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">eBay Monitor MVP</p>
          <h1>商品与店铺监控台</h1>
          <p className="muted-note">访问口令校验后才能进入系统。</p>
        </div>
        <div className="header-actions">
          <nav className="nav">
            <NavLink to="/items">商品列表</NavLink>
            <NavLink to="/items/new">新增商品</NavLink>
            <NavLink to="/shops">店铺列表</NavLink>
            <NavLink to="/alerts">预警中心</NavLink>
          </nav>
          <button type="button" className="ghost-button" onClick={handleLogout}>
            退出访问
          </button>
        </div>
      </header>
      <main className="workspace">
        <Outlet />
      </main>
    </div>
  );
}
