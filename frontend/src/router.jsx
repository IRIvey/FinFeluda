import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { Navbar } from "./components/layout/Navbar";
import { HomePage } from "./pages/HomePage";

function RootLayout() {
  return (
    <div className="min-h-screen bg-paper">
      <Navbar />
      <Outlet />
    </div>
  );
}

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
