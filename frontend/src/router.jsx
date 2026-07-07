import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { Navbar } from "./components/layout/Navbar";
import { HomePage } from "./pages/HomePage";
import { NewInvestigationPage } from "./pages/NewInvestigationPage";
import { ProcessingPage } from "./pages/ProcessingPage";
import { InvestigationPage } from "./pages/InvestigationPage";
import { ChatPage } from "./pages/ChatPage";
import { ReportPage } from "./pages/ReportPage";
import { ComparePage } from "./pages/ComparePage";
import { SourcesPage } from "./pages/SourcesPage";
import { RiskCategoryPage } from "./pages/RiskCategoryPage";

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
      { path: "/new", element: <NewInvestigationPage /> },
      { path: "/investigations/:id/processing", element: <ProcessingPage /> },
      { path: "/investigations/:id", element: <InvestigationPage /> },
      { path: "/investigations/:id/sources", element: <SourcesPage /> },
      { path: "/investigations/:id/risks/:category", element: <RiskCategoryPage /> },
      { path: "/investigations/:id/chat", element: <ChatPage /> },
      { path: "/investigations/:id/report", element: <ReportPage /> },
      { path: "/compare", element: <ComparePage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
