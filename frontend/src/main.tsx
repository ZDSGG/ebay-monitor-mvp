import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { RequireAuth } from "./components/RequireAuth";
import { ItemCreatePage } from "./pages/ItemCreatePage";
import { ItemDetailPage } from "./pages/ItemDetailPage";
import { ItemListPage } from "./pages/ItemListPage";
import { LoginPage } from "./pages/LoginPage";
import { AppShell } from "./shell/AppShell";
import "./styles.css";

const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/items" replace /> },
          { path: "/items", element: <ItemListPage /> },
          { path: "/items/new", element: <ItemCreatePage /> },
          { path: "/items/:itemId", element: <ItemDetailPage /> },
        ],
      },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
