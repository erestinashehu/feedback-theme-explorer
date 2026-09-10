import { NavLink, Routes, Route, Navigate } from "react-router-dom";
import UploadPage from "./pages/UploadPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import SearchPage from "./pages/SearchPage.jsx";

const tabs = [
  { to: "/dashboard", label: "Dashboard", num: "01" },
  { to: "/upload", label: "Upload feedback", num: "02" },
  { to: "/search", label: "Ask", num: "03" },
];

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="masthead-rule bg-paper px-6 pt-6 pb-3 md:px-10">
        <div className="max-w-6xl mx-auto flex items-baseline justify-between flex-wrap gap-2">
          <h1 className="font-sans text-3xl md:text-4xl font-normal">
            Feedback Explorer
          </h1>
        </div>
      </header>

      <nav className="border-b hairline bg-paper px-6 md:px-10">
        <div className="max-w-6xl mx-auto flex gap-8">
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) =>
                `py-3 text-sm flex items-center gap-2 border-b-2 -mb-px transition-colors ${
                  isActive
                    ? "border-ochre text-ink"
                    : "border-transparent text-muted hover:text-ink"
                }`
              }
            >
              {t.label}
            </NavLink>
          ))}
        </div>
      </nav>

      <main className="flex-1 px-6 md:px-10 py-8">
        <div className="max-w-6xl mx-auto w-full">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/search" element={<SearchPage />} />
          </Routes>
        </div>
      </main>

      <footer className="border-t hairline px-6 md:px-10 py-4">
      </footer>
    </div>
  );
}