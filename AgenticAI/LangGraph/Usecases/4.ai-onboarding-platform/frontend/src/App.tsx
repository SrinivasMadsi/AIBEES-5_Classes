import { Link, Route, Routes, useLocation } from "react-router-dom";
import { Database, FileText, ListChecks, Shield, Workflow } from "lucide-react";
import FormsListPage from "./pages/FormsListPage";
import FormFillPage from "./pages/FormFillPage";
import SubmissionsListPage from "./pages/SubmissionsListPage";
import ValidationResultsPage from "./pages/ValidationResultsPage";
import BOMQueuePage from "./pages/BOMQueuePage";
import BOMReviewPage from "./pages/BOMReviewPage";

function App() {
  const loc = useLocation();

  const navItem = (to: string, icon: React.ReactNode, label: string) => {
    const active = loc.pathname.startsWith(to);
    return (
      <Link
        to={to}
        className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
          active
            ? "bg-slate-900 text-white"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
        }`}
      >
        {icon}
        {label}
      </Link>
    );
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col">
        <div className="px-6 py-5 border-b border-slate-200">
          <div className="flex items-center gap-2 font-display font-bold text-lg text-slate-900">
            <Workflow className="w-5 h-5 text-blue-600" />
            AI Onboarding
          </div>
          <div className="text-xs text-slate-500 mt-1">Platform</div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <div className="px-3 py-1 text-xs uppercase tracking-wide text-slate-400 font-semibold">
            IPM
          </div>
          {navItem("/forms", <FileText className="w-4 h-4" />, "Forms")}
          {navItem("/submissions", <Database className="w-4 h-4" />, "My Submissions")}

          <div className="px-3 py-1 mt-4 text-xs uppercase tracking-wide text-slate-400 font-semibold">
            BOM Analyst
          </div>
          {navItem("/bom/queue", <ListChecks className="w-4 h-4" />, "Review Queue")}
        </nav>

        <div className="px-4 py-3 border-t border-slate-200 text-xs text-slate-500 flex items-center gap-2">
          <Shield className="w-3 h-3" />
          AIBees Academy demo
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<FormsListPage />} />
          <Route path="/forms" element={<FormsListPage />} />
          <Route path="/forms/:formId/fill" element={<FormFillPage />} />
          <Route path="/submissions" element={<SubmissionsListPage />} />
          <Route path="/submissions/:submissionId" element={<ValidationResultsPage />} />
          <Route path="/bom/queue" element={<BOMQueuePage />} />
          <Route path="/bom/reviews/:reviewId" element={<BOMReviewPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
