import { NavLink, Outlet } from "react-router-dom";

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">eBay Monitor MVP</p>
          <h1>商品价格监控台</h1>
        </div>
        <nav className="nav">
          <NavLink to="/items">商品列表</NavLink>
          <NavLink to="/items/new">新增商品</NavLink>
        </nav>
      </header>
      <main className="workspace">
        <Outlet />
      </main>
    </div>
  );
}
